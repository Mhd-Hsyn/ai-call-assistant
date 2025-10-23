import json
import pandas as pd
import numpy as np
from io import BytesIO
from datetime import datetime
from dateutil import parser
from retell import Retell
from fastapi import UploadFile
from app.config.settings import settings
from app.client.models import CallModel, AgentModel
from app.auth.models import UserModel
from app.core.exceptions.base import (
    AppException, 
    InternalServerErrorException,
    NotFoundException,
)
from app.config.logger import get_logger
from app.core.utils.helpers import (
    parse_timestamp,
    get_day_with_suffix,
)

logger = get_logger("Retell Call Service")



class CallFileService:
    """
    Service for handling Excel/CSV file parsing
    """

    @staticmethod
    async def parse_uploaded_file(file: UploadFile):
        try:
            contents = await file.read()
            file_ext = file.filename.split(".")[-1].lower()

            # Read file using pandas
            if file_ext == "csv":
                df = pd.read_csv(BytesIO(contents))
            elif file_ext in ["xls", "xlsx"]:
                df = pd.read_excel(BytesIO(contents))
            else:
                raise AppException("Invalid file type. Only CSV or Excel supported.")

            # Clean column names
            df.columns = (
                df.columns.str.strip()
                .str.lower()
                .str.replace(" ", "_")
            )

            # Replace NaN with empty string
            df = df.replace({np.nan: ""})

            # Convert DataFrame to list of dicts
            records = df.astype(object).to_dict(orient="records")

            # Clean and normalize values
            for record in records:
                for k, v in record.items():

                    # Handle pandas datetime safely
                    if isinstance(v, (datetime, pd.Timestamp)):
                        if pd.isna(v):  # skip NaT
                            record[k] = ""
                        else:
                            day = get_day_with_suffix(v.day)
                            record[k] = f"{day} {v.strftime('%b, %Y')}"  # 1st Oct, 2025
                        continue

                    # Handle int
                    if isinstance(v, (np.integer, int)):
                        record[k] = str(int(v))
                        continue

                    # Handle float
                    if isinstance(v, (np.floating, float)):
                        record[k] = str(int(v)) if str(v).endswith(".0") else str(v)
                        continue

                    # Handle string
                    if isinstance(v, str):
                        val = v.strip()
                        if val:
                            try:
                                parsed = parser.parse(val, fuzzy=True, dayfirst=False)
                                record[k] = parsed.strftime("%b %d, %Y")
                            except Exception:
                                record[k] = val
                        else:
                            record[k] = ""
                        continue

                    # Handle NaN or None
                    if pd.isna(v):
                        record[k] = ""

            return records

        except Exception as e:
            raise InternalServerErrorException(f"File parse failed: {str(e)}")




class RetellCallService:
    def __init__(self):
        self.client = Retell(api_key=settings.retell_api_key)

    async def create_phone_call(self, *, user: UserModel, payload: dict) -> CallModel:
        """
        Create a phone call in Retell and store it in DB.
        """
        logger.info("Creating Retell phone call...")

        try:
            response = self.client.call.create_phone_call(
                from_number=payload["from_number"],
                to_number=payload["to_number"],
                override_agent_id=payload.get("override_agent_id"),
                retell_llm_dynamic_variables=payload.get("retell_llm_dynamic_variables", {}),
            )

            # logger.debug(f"Retell response: {json.dumps(response, indent=2)}")

            # --- Extract agent details
            agent_id = response.agent_id
            agent = await AgentModel.find_one(AgentModel.agent_id == agent_id)

            # --- Create CallModel entry
            new_call = CallModel(
                user=user,
                agent=agent,
                agent_name=response.agent_name,
                agent_retell_id=response.agent_id,
                call_id=response.call_id,
                call_type=response.call_type,
                direction=response.direction,
                call_status=response.call_status,
                from_number=response.from_number,
                to_number=response.to_number,
                metadata=response.metadata,
                retell_llm_dynamic_variables=response.retell_llm_dynamic_variables,
                collected_dynamic_variables=response.collected_dynamic_variables,
                start_timestamp=parse_timestamp(response.start_timestamp),
                end_timestamp=parse_timestamp(response.end_timestamp),
                duration_ms=response.duration_ms,
            )

            await new_call.insert()

            logger.info(f"Retell call created and saved | call_id={new_call.call_id}")
            return new_call

        except Exception as e:
            logger.exception(f"Failed to create Retell call: {str(e)}")
            raise


class RetellWebhookService:
    def __init__(self):
        self.handlers = {
            "call_started": self._handle_started,
            "call_ended": self._handle_ended,
            "call_analyzed": self._handle_analyzed,
        }
        self.logger = get_logger("Retell Webhook Service")

    async def handle_event(self, payload: dict):
        """Main entrypoint for webhook event handling."""
        self.logger.info("Received Retell webhook")
        self.logger.debug(f"Payload: {json.dumps(payload, indent=2)}")

        event = payload.get("event")
        call_data = payload.get("call", {})

        if not event:
            raise AppException("Missing 'event' in payload")

        call_id = call_data.get("call_id")
        if not call_id:
            raise AppException("Missing 'call_id' in payload")

        existing = await CallModel.find_one(CallModel.call_id == call_id)
        handler = self.handlers.get(event)

        if not handler:
            self.logger.warning(f"Unhandled event type: {event}")
            return {"success": False, "message": f"Unhandled event: {event}"}

        return await handler(call_data, existing, call_id)

    # Helpers
    def _parse_time(self, value):
        return parse_timestamp(value) or datetime.utcnow()


    async def _get_agent_and_user(self, agent_id):
        agent = await AgentModel.find_one(AgentModel.agent_id == agent_id, fetch_links=True)
        if not agent:
            raise NotFoundException("Agent not found")
        if not agent.user:
            raise AppException("Agent not linked to any user")

        user = await UserModel.get(agent.user.id)
        return agent, user


    async def _update_fields(self, obj, data: dict, fields: list[str]):
        for field in fields:
            if field in data:
                value = data[field]
                # Don’t overwrite existing with None
                if value is not None:
                    setattr(obj, field, value)
        await obj.save()


    # Event Handlers
    async def _handle_started(self, call_data, existing, call_id):
        start_time = self._parse_time(call_data.get("start_timestamp"))

        if not existing:
            agent, user = await self._get_agent_and_user(call_data["agent_id"])
            call = CallModel(
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
                metadata=call_data.get("metadata", {}),
                retell_llm_dynamic_variables=call_data.get("retell_llm_dynamic_variables", {}),
            )
            await call.insert()
            self.logger.info(f"New call created successfully (call_id={call_id})")
            return {"success": True, "message": "New call created"}

        existing.start_timestamp = start_time
        await self._update_fields(existing, call_data, ["call_status", "metadata", "retell_llm_dynamic_variables"])
        self.logger.info(f"Existing call updated successfully (call_id={call_id})")
        return {"success": True, "message": "Existing call updated"}


    async def _handle_ended(self, call_data, existing, call_id):
        if not existing:
            return {"success": False, "message": "Call not found for call_ended event"}

        existing.start_timestamp = self._parse_time(call_data.get("start_timestamp"))
        existing.end_timestamp = self._parse_time(call_data.get("end_timestamp"))

        await self._update_fields(existing, call_data, [
            "call_status",
            "duration_ms",
            "recording_url",
            "recording_multi_channel_url",
            "disconnection_reason",
            "public_log_url",
            "scrubbed_recording_url",
            "scrubbed_recording_multi_channel_url",
            "transcript",
            "transcript_object",
            "transcript_with_tool_calls",
            "scrubbed_transcript_with_tool_calls",
            "call_cost",
            "llm_token_usage",
            "retell_llm_dynamic_variables",
        ])
        self.logger.info(f"Call marked as ended successfully (call_id={call_id})")
        return {"success": True, "message": "Call updated as ended"}


    async def _handle_analyzed(self, call_data, existing, call_id):
        if not existing:
            return {"success": False, "message": "Call not found for call_analyzed event"}

        existing.start_timestamp = self._parse_time(call_data.get("start_timestamp"))
        existing.end_timestamp = self._parse_time(call_data.get("end_timestamp"))

        await self._update_fields(existing, call_data, [
            "call_status",
            "duration_ms",
            "call_analysis",
            "call_cost",
            "disconnection_reason",
            "transcript_object",
            "transcript_with_tool_calls",
            "llm_token_usage",
            "transcript",
            "recording_url",
            "recording_multi_channel_url",
            "public_log_url",
            "retell_llm_dynamic_variables",
        ])
        self.logger.info(f"Call analyzed data saved successfully (call_id={call_id})")
        return {"success": True, "message": "Call analysis updated successfully"}




