import json
from retell import Retell
from app.config.settings import settings
from app.client.models import CallModel, AgentModel
from app.auth.models import UserModel
from app.config.logger import get_logger
from datetime import datetime
from app.core.utils.helpers import (
    parse_timestamp
)

logger = get_logger("Retell Service")


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

            logger.info(f"✅ Retell call created and saved | call_id={new_call.call_id}")
            return new_call

        except Exception as e:
            logger.exception(f"Failed to create Retell call: {str(e)}")
            raise


