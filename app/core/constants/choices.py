from enum import IntEnum, StrEnum

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



