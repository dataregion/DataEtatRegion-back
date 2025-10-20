from typing import Literal
from pydantic import BaseModel

MAT_VIEWS_REFRESHED_EVENT_CHANNEL = "refresh_materialized_views:events"
_MAT_VIEWS_REFRESHED_EVENT_TYPE = Literal["materialized_views_refreshed"]


class MaterializedViewsRefreshed(BaseModel):
    channel: str = MAT_VIEWS_REFRESHED_EVENT_CHANNEL
    type: _MAT_VIEWS_REFRESHED_EVENT_TYPE
