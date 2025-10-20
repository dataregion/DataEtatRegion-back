from pydantic import BaseModel

MAT_VIEWS_REFRESHED_EVENT_CHANNEL = "materialized_views:events"
class MaterializedViewsRefreshed(BaseModel):
    type: str = MAT_VIEWS_REFRESHED_EVENT_CHANNEL
