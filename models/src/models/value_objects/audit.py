from enum import StrEnum, auto


class RefreshMaterializedViewsEvent(StrEnum):
    BEGIN = auto()
    ENDED = auto()