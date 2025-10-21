import pandas as pd
import numpy as np
from io import BytesIO
from fastapi import UploadFile
from retell import Retell
from app.config.settings import settings
from app.client.models import CallModel, AgentModel
from app.auth.models import UserModel
from app.core.exceptions.base import (
    AppException, 
    InternalServerErrorException
)
from app.config.logger import get_logger
from app.core.utils.helpers import (
    parse_timestamp
)

logger = get_logger("Retell Service")




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

            # Replace NaN with empty string
            df = df.replace({np.nan: ""})

            # Convert all numpy datatypes to native Python types
            records = df.astype(object).to_dict(orient="records")

            # Ensure all keys/values are basic serializable types
            for record in records:
                for k, v in record.items():
                    if isinstance(v, (np.integer, np.floating)):
                        record[k] = v.item()
                    elif pd.isna(v):
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

            logger.info(f"✅ Retell call created and saved | call_id={new_call.call_id}")
            return new_call

        except Exception as e:
            logger.exception(f"Failed to create Retell call: {str(e)}")
            raise


