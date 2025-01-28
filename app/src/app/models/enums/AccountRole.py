from enum import StrEnum


class AccountRole(StrEnum):
    ADMIN = "ADMIN"
    USER = "USER"
    COMPTABLE = "COMPTABLE"
    COMPTABLE_NATIONAL = "COMPTABLE_NATIONAL"
