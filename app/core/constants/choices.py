from enum import IntEnum
from enum_tools import StrEnum

class UserRoleChoices(IntEnum):
    SUPER_ADMIN = 1
    CLIENT = 2

class UserAccountStatusChoices(IntEnum):
    INACTIVE = 0
    ACTIVE = 1
    DEACTIVATED = 2
    SUSPENDED = 3
    PENDING = 4
    DELETED = 5


class OTPScenarioChoices(IntEnum):
    RESET_USER_PASSWORD = 1
    VERIFY_USER_EMAIL = 2



#### Retail Model ####

class KnowledgeBaseStatusChoices(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETE = "complete"
    ERROR = "error"


class KnowledgeBaseSourceTypeChoices(StrEnum):
    DOCUMENT = "document"
    TEXT = "text"
    URL = "url"


class LanguageChoices(StrEnum):
    EN_US = "en-US"
    EN_IN = "en-IN"
    EN_GB = "en-GB"
    EN_AU = "en-AU"
    EN_NZ = "en-NZ"
    DE_DE = "de-DE"
    ES_ES = "es-ES"
    ES_419 = "es-419"
    HI_IN = "hi-IN"
    FR_FR = "fr-FR"
    FR_CA = "fr-CA"
    JA_JP = "ja-JP"
    PT_PT = "pt-PT"
    PT_BR = "pt-BR"
    ZH_CN = "zh-CN"
    RU_RU = "ru-RU"
    IT_IT = "it-IT"
    KO_KR = "ko-KR"
    NL_NL = "nl-NL"
    NL_BE = "nl-BE"
    PL_PL = "pl-PL"
    TR_TR = "tr-TR"
    TH_TH = "th-TH"
    VI_VN = "vi-VN"
    RO_RO = "ro-RO"
    BG_BG = "bg-BG"
    CA_ES = "ca-ES"
    DA_DK = "da-DK"
    FI_FI = "fi-FI"
    EL_GR = "el-GR"
    HU_HU = "hu-HU"
    ID_ID = "id-ID"
    NO_NO = "no-NO"
    SK_SK = "sk-SK"
    SV_SE = "sv-SE"
    MULTI = "multi"


class VoiceModelChoices(StrEnum):
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    GPT_4_1 = "gpt-4.1"
    GPT_4_1_MINI = "gpt-4.1-mini"
    GPT_4_1_NANO = "gpt-4.1-nano"
    GPT_5 = "gpt-5"
    GPT_5_MINI = "gpt-5-mini"
    GPT_5_NANO = "gpt-5-nano"
    CLAUDE_4_0_SONNET = "claude-4.0-sonnet"
    CLAUDE_3_7_SONNET = "claude-3.7-sonnet"
    CLAUDE_3_5_HAIKU = "claude-3.5-haiku"
    GEMINI_2_0_FLASH = "gemini-2.0-flash"
    GEMINI_2_0_FLASH_LITE = "gemini-2.0-flash-lite"
    GEMINI_2_5_FLASH = "gemini-2.5-flash"
    GEMINI_2_5_FLASH_LITE = "gemini-2.5-flash-lite"


class EngineStartSpeakChoice(StrEnum):
    AGENT = 'agent'
    USER = 'user'


class CallStatusChoices(StrEnum):
    REGISTERED = 'registered'
    NOT_CONNECTED = 'not_connected'
    ONGOING = 'ongoing'
    ENDED = 'ended'
    ERROR = 'error'


class CallDirectionChoices(StrEnum):
    INBOUND = 'inbound'
    OUTBOUND = 'outbound'


class CallTypeChoices(StrEnum):
    PHONE_CALL = 'phone_call'
    WEB_CALL = 'web_call'


class CallDisconnectionReasonChoices(StrEnum):
    USER_HANGUP = "user_hangup"
    AGENT_HANGUP = "agent_hangup"
    CALL_TRANSFER = "call_transfer"
    VOICEMAIL_REACHED = "voicemail_reached"
    INACTIVITY = "inactivity"
    MAX_DURATION_REACHED = "max_duration_reached"
    CONCURRENCY_LIMIT_REACHED = "concurrency_limit_reached"
    NO_VALID_PAYMENT = "no_valid_payment"
    SCAM_DETECTED = "scam_detected"
    DIAL_BUSY = "dial_busy"
    DIAL_FAILED = "dial_failed"
    DIAL_NO_ANSWER = "dial_no_answer"
    INVALID_DESTINATION = "invalid_destination"
    TELEPHONY_PROVIDER_PERMISSION_DENIED = "telephony_provider_permission_denied"
    TELEPHONY_PROVIDER_UNAVAILABLE = "telephony_provider_unavailable"
    SIP_ROUTING_ERROR = "sip_routing_error"
    MARKED_AS_SPAM = "marked_as_spam"
    USER_DECLINED = "user_declined"
    ERROR_LLM_WEBSOCKET_OPEN = "error_llm_websocket_open"
    ERROR_LLM_WEBSOCKET_LOST_CONNECTION = "error_llm_websocket_lost_connection"
    ERROR_LLM_WEBSOCKET_RUNTIME = "error_llm_websocket_runtime"
    ERROR_LLM_WEBSOCKET_CORRUPT_PAYLOAD = "error_llm_websocket_corrupt_payload"
    ERROR_NO_AUDIO_RECEIVED = "error_no_audio_received"
    ERROR_ASR = "error_asr"
    ERROR_RETELL = "error_retell"
    ERROR_UNKNOWN = "error_unknown"
    ERROR_USER_NOT_JOINED = "error_user_not_joined"
    REGISTERED_CALL_TIMEOUT = "registered_call_timeout"

