from enum import IntEnum

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
