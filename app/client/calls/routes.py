import json
from datetime import datetime
from fastapi import (
    APIRouter, 
    status, 
    UploadFile, 
    File,
    Depends, 
)
from app.config.settings import settings
from app.core.exceptions.base import (
    AppException,
    NotFoundException

)
from app.core.dependencies.authorization import (
    ProfileActive
)
from app.auth.models import (
    UserModel
)
from ..models import (
    AgentModel,
    CallModel
)
from .schemas import (
    APIBaseResponse,
    CallInitializeSchema,
)
from .services import (
    RetellCallService,
    CallFileService
)
from app.core.utils.helpers import (
    parse_timestamp
)
from app.config.logger import get_logger


logger = get_logger("Calling Routes")

calls_router = APIRouter()



@calls_router.post(
    "/parse-file",
    response_model=APIBaseResponse,
    status_code=status.HTTP_200_OK,
)
async def parse_file(file: UploadFile = File(...)):
    """
    Upload Excel or CSV file → Get array of key-value objects
    """
    records = await CallFileService.parse_uploaded_file(file)
    return APIBaseResponse(
        status=True,
        message="File parsed successfully",
        data=records
    )



@calls_router.post(
    "/initialize-call",
    response_model=APIBaseResponse,
    status_code=status.HTTP_201_CREATED,
)
async def initialize_call(
    payload: CallInitializeSchema,
    user: UserModel = Depends(ProfileActive()),
):
    """
    Initialize a phone call through Retell and store it in DB.
    """
    service = RetellCallService()
    new_call = await service.create_phone_call(user=user, payload=payload.dict(by_alias=True))

    return APIBaseResponse(
        status=True,
        message="Call initialized successfully",
        data={
            "call_id": new_call.call_id, 
            "agent_id": new_call.agent_retell_id
        }
    )
    





# {{BASE_URL}}/api/clientside/calls/retell/webhook
@calls_router.post("/retell/webhook")
async def retell_webhook(payload: dict):
    """
    Handles Retell call lifecycle webhooks.
    Logs full event lifecycle (start/end/analyze) and syncs with DB.
    """
    logger.info("Received Retell webhook")

    # Log payload (for debugging)
    logger.debug(f"Raw payload: {json.dumps(payload, indent=2)}")

    event = payload.get("event")
    call_data = payload.get("call", {})

    if not event:
        logger.warning("Missing 'event' field in payload")
        raise AppException("Missing 'event' in payload")

    call_id = call_data.get("call_id")
    if not call_id:
        logger.warning("Missing 'call_id' in payload")
        raise AppException("Missing 'call_id' in payload")

    logger.info(f"Event received: {event} | Call ID: {call_id}")

    # Try to find existing record
    existing = await CallModel.find_one(CallModel.call_id == call_id)
    logger.debug(f"Existing call found: {bool(existing)}")

    if event == "call_started":
        raw_timestamp = call_data.get("start_timestamp")
        start_time = parse_timestamp(raw_timestamp)
        logger.info(f"Raw timestamp: {raw_timestamp} | Parsed datetime: {start_time}")

        if not start_time:
            logger.error(f"Invalid start_timestamp: {raw_timestamp}")
            raise AppException(f"Invalid start_timestamp: {raw_timestamp}")

        if not existing:
            # Find related Agent
            agent_id = call_data.get("agent_id")
            logger.info(f"Looking up Agent ID: {agent_id}")
            agent = await AgentModel.find_one(AgentModel.agent_id == agent_id)

            if not agent:
                logger.error(f"Agent not found in DB (agent_id={agent_id})")
                raise NotFoundException("Agent not found in DB")

            if not agent.user:
                logger.error(f"Agent {agent_id} not linked with any user")
                raise AppException("Agent not linked with any user")

            # Link with user via agent
            user = await UserModel.get(agent.user.id) if agent.user else None
            logger.info(f"Linked user ID: {user.id if user else 'None'}")

            # Extract metadata safely
            metadata = call_data.get("metadata", {})
            retell_vars = call_data.get("retell_llm_dynamic_variables", {})

            new_call = CallModel(
                user=user,
                agent=agent,
                call_id=call_id,
                agent_name=call_data.get("agent_name"),
                agent_retell_id=call_data.get("agent_id"),
                call_type=call_data.get("call_type"),
                direction=call_data.get("direction"),
                call_status=call_data.get("call_status"),
                disconnection_reason=call_data.get("disconnection_reason"),
                from_number=call_data.get("from_number"),
                to_number=call_data.get("to_number"),
                start_timestamp=start_time,
                metadata=metadata,
                retell_llm_dynamic_variables=retell_vars,
            )

            await new_call.insert()
            logger.info(f"New call created successfully (call_id={call_id})")
            return {"success": True, "message": "New call created"}

        else:
            # Update existing record
            existing.call_status = call_data.get("call_status")
            existing.start_timestamp = start_time
            existing.metadata = call_data.get("metadata", {})
            await existing.save()

            logger.info(f"Existing call updated successfully (call_id={call_id})")
            return {"success": True, "message": "Existing call updated"}


    elif event == "call_ended":
        if not existing:
            logger.warning(f"No existing call found for call_ended event (call_id={call_id})")
            return {"success": False, "message": "Call not found for call_ended event"}

        # Safely parse timestamps
        raw_end = call_data.get("end_timestamp")
        end_time = parse_timestamp(raw_end)
        if not end_time:
            logger.warning(f"Invalid or missing end_timestamp for call_id={call_id}")
            end_time = datetime.utcnow()

        # Update fields with validation
        existing.call_status = "ended"
        existing.end_timestamp = end_time
        existing.duration_ms = call_data.get("duration_ms")
        existing.transcript = call_data.get("transcript")
        existing.recording_url = call_data.get("recording_url")
        existing.recording_multi_channel_url = call_data.get("recording_multi_channel_url")
        existing.public_log_url = call_data.get("public_log_url")
        existing.scrubbed_recording_url = call_data.get("scrubbed_recording_url")
        existing.scrubbed_recording_multi_channel_url = call_data.get("scrubbed_recording_multi_channel_url")
        existing.transcript_object = call_data.get("transcript_object", [])
        existing.transcript_with_tool_calls = call_data.get("transcript_with_tool_calls", [])
        existing.scrubbed_transcript_with_tool_calls = call_data.get("scrubbed_transcript_with_tool_calls", [])
        existing.call_analysis = call_data.get("call_analysis", {})
        existing.call_cost = call_data.get("call_cost", {})
        existing.llm_token_usage = call_data.get("llm_token_usage", {})

        await existing.save()
        logger.info(f"Call marked as ended successfully (call_id={call_id})")

        return {"success": True, "message": "Call updated as ended"}


    elif event == "call_analyzed":
        if not existing:
            logger.warning(f"No existing call found for call_analyzed event (call_id={call_id})")
            return {"success": False, "message": "Call not found for call_analyzed event"}

        # Update analysis-related fields
        existing.call_analysis = call_data.get("call_analysis", {})
        existing.call_cost = call_data.get("call_cost", {})
        existing.llm_token_usage = call_data.get("llm_token_usage", {})
        existing.transcript = call_data.get("transcript") or existing.transcript
        existing.transcript_object = call_data.get("transcript_object") or existing.transcript_object
        existing.transcript_with_tool_calls = call_data.get("transcript_with_tool_calls") or existing.transcript_with_tool_calls
        existing.recording_url = call_data.get("recording_url") or existing.recording_url
        existing.recording_multi_channel_url = call_data.get("recording_multi_channel_url") or existing.recording_multi_channel_url
        existing.public_log_url = call_data.get("public_log_url") or existing.public_log_url

        # Don’t overwrite metadata or retell_llm_dynamic_variables
        await existing.save()

        logger.info(f"Call analyzed data saved successfully (call_id={call_id})")
        return {"success": True, "message": "Call analysis updated successfully"}


