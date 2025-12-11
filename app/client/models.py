from datetime import datetime
from bson.decimal128 import Decimal128
from decimal import Decimal, InvalidOperation
from beanie import Link, before_event, Delete
from pydantic import EmailStr, Field, model_validator
from typing import Optional, List, Dict, Any
from app.core.models.base import BaseDocument
from app.auth.models import UserModel
from app.core.constants.choices import (
    KnowledgeBaseStatusChoices,
    KnowledgeBaseSourceTypeChoices,
    VoiceModelChoices,
    LanguageChoices,
    EngineStartSpeakChoice,
    CallStatusChoices,
    CallDirectionChoices,
    CallTypeChoices,
    CallDisconnectionReasonChoices,
    UserSentimentChoices,

)
from app.config.logger import get_logger

logger = get_logger("Client Models")



class KnowledgeBaseModel(BaseDocument):
    user: Link[UserModel]
    knowledge_base_id: str = Field(..., index=True, unique=True)
    name: str
    status: KnowledgeBaseStatusChoices = KnowledgeBaseStatusChoices.IN_PROGRESS

    class Settings:
        name = "knowledge_bases"


    @before_event(Delete)
    async def delete_related_sources_and_references(self):
        # Delete related KnowledgeBaseSourceModel
        await KnowledgeBaseSourceModel.find(
            KnowledgeBaseSourceModel.knowledge_base.id == self.id
        ).delete_many()

        # Remove this KB id from ResponseEngineModel.knowledge_base_ids arrays
        await ResponseEngineModel.find(
            ResponseEngineModel.knowledge_base_ids == self.knowledge_base_id
        ).update_many(
            {"$pull": {"knowledge_base_ids": self.knowledge_base_id}}
        )


class KnowledgeBaseSourceModel(BaseDocument):
    knowledge_base: Link[KnowledgeBaseModel]
    source_id: str = Field(..., index=True, unique=True)
    type : KnowledgeBaseSourceTypeChoices
    title : str | None = None
    url : str

    class Settings:
        name = "knowledge_base_sources"



class ResponseEngineModel(BaseDocument):
    """
    Stores user-specific Retell LLM (Response Engine) configuration and metadata.
    """

    user: Link[UserModel]
    engine_id: str = Field(..., index=True, unique=True, description="ID from Retell API")
    general_prompt: str = None
    knowledge_base_ids: Optional[List[str]] = Field(default_factory=list)
    temperature: float = 0
    start_speaker: EngineStartSpeakChoice = Field(
        default=EngineStartSpeakChoice.USER,
        description="Who start conversation"
    )
    voice_model: VoiceModelChoices = Field(
        default=VoiceModelChoices.GPT_4O_MINI,
        description="Voice model variant"
    )

    class Settings:
        name = "response_engines"


class AgentModel(BaseDocument):
    """
    Represents a user's agent linked to a Retell Response Engine.
    """

    user: Link[UserModel]
    response_engine: Link[ResponseEngineModel]
    agent_id: str = Field(..., index=True, unique=True, description="Agent ID from Retell API")
    agent_name: str = Field(..., description="Agent name shown in the app")
    voice_id: str = Field(..., description="Selected voice ID from Retell /voices API")
    voice_id_data: Optional[Dict[str, Any]] = Field(default=None, description="Full voice metadata object")
    language: LanguageChoices = Field(
        default=LanguageChoices.EN_US,
        description="Language code (e.g. en-US, es-ES, fr-FR)"
    )

    class Settings:
        name = "agents"


class MeetingWorkflowModel(BaseDocument):
    """
    Stores both the original incoming payload (raw_data) and the normalized states
    we use internally. Also store engine_id for fast lookups.
    """
    agent: Link[AgentModel]
    engine_id: str  # quick reference to response_engine.engine_id
    raw_payload: Dict[str, Any]   # save exactly the incoming payload
    states_normalized: List[Dict[str, Any]]  # normalized internal copy (optional)

    class Settings:
        name = "meeting_workflows"



class CampaignModel(BaseDocument):

    user : Link[UserModel]
    agent : Link[AgentModel]
    name : str = Field(..., description="Name of the Campaign")
    is_deleted: bool = Field(default=False, description="Soft delete flag")

    class Settings:
        name = "campaigns"


class CampaignContactsModel(BaseDocument):

    user : Link[UserModel]
    campaign : Link[CampaignModel]
    phone_number : str = Field(..., description="Phone Number")
    first_name : Optional[str] = Field(default=None, description="First Name of the Contatct")
    last_name : Optional[str] = Field(default=None, description="Last Name of the Contatct")
    email : Optional[EmailStr] = Field(default=None, description="Email of the Contatct")
    no_of_calls : int = Field(default=0, description="No of calls per contact")
    dynamic_variables: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom dynamic fields for contact")

    class Settings:
        name = "campaign_contacts"
        indexes = [
            [("campaign", 1), ("phone_number", 1)],  # unique per campaign
        ]

    async def increment_call_count(self):
        """Increment number of calls for this contact."""
        self.no_of_calls += 1
        await self.save()


class CallModel(BaseDocument):
    """
    Stores all Retell phone call details, synced from webhooks or Retell API.
    """

    # Relations
    user: Link[UserModel]
    agent: Link[AgentModel]
    campaign_contact: Optional[Link["CampaignContactsModel"]] = Field(default=None, description="Optional link to campaign contact")

    # Identifiers
    agent_name : str 
    agent_retell_id : str
    call_id: str = Field(..., index=True, unique=True)
    call_type: CallTypeChoices = Field(default=CallTypeChoices.PHONE_CALL, description= 'call type (phone-call or web-call)')
    direction: CallDirectionChoices
    call_status: CallStatusChoices = Field(default=CallStatusChoices.REGISTERED, description= 'call status')
    disconnection_reason: Optional[CallDisconnectionReasonChoices] = Field(default=None,description="Call disconnection reason")

    # Numbers
    from_number: Optional[str] = None
    to_number: Optional[str] = None

    # Timestamps
    start_timestamp: Optional[datetime] = None
    end_timestamp: Optional[datetime] = None
    duration_ms: Optional[int] = None

    # Meta + Identifiers
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    retell_llm_dynamic_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)
    collected_dynamic_variables: Optional[Dict[str, Any]] = Field(default_factory=dict)

    # URLs (recordings, transcripts, logs)
    recording_url: Optional[str] = None
    recording_multi_channel_url: Optional[str] = None
    scrubbed_recording_url: Optional[str] = None
    scrubbed_recording_multi_channel_url: Optional[str] = None
    public_log_url: Optional[str] = None
    knowledge_base_retrieved_contents_url: Optional[str] = None

    # Transcript
    transcript: Optional[str] = None
    transcript_object: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    transcript_with_tool_calls: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    scrubbed_transcript_with_tool_calls: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    # Consting
    call_cost: Optional[Dict[str, Any]] = Field(default_factory=dict)
    total_duration : Optional[int] = Field(default=None, description="Total duration in seconds")
    total_duration_unit_price : Optional[Decimal] = Field(default=Decimal("0.0"), description="Total duration in seconds")
    combined_cost : Optional[Decimal] = Field(default=Decimal("0.0"), description="Total cost in cents")

    # Analysis
    call_analysis: Optional[Dict[str, Any]] = Field(default_factory=dict)
    llm_token_usage: Optional[Dict[str, Any]] = Field(default_factory=dict)
    user_sentiment : Optional[UserSentimentChoices] = Field(default=None,description="User Sentiment Enums")
    call_successful : Optional[bool] = Field(default=None,description="User Call Successful or Unsuccessful")

    class Settings:
        name = "calls"

    def __repr__(self):
        return f"<Call {self.call_id} ({self.call_status})>"


    @model_validator(mode="before")
    @classmethod
    def convert_decimal128_to_decimal(cls, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Decimal128 fields to Decimal for Pydantic validation.
        Logs conversion errors and skips invalid fields.
        """
        # Get all fields annotated as Decimal from the model
        decimal_fields = [
            field_name
            for field_name, field_info in cls.model_fields.items()
            if field_info.annotation is Decimal or field_info.annotation == Optional[Decimal]
        ]

        for field in decimal_fields:
            if field in data and isinstance(data[field], Decimal128):
                try:
                    data[field] = Decimal(str(data[field]))
                except InvalidOperation as e:
                    logger.error(f"Failed to convert Decimal128 to Decimal for field '{field}': {data[field]}, error: {e}")
                    data[field] = None  # Or set a default value, e.g., Decimal("0.0")

        return data



