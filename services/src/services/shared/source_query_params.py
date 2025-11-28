from functools import cached_property
from typing import Optional
from pydantic import Field, computed_field

from models.value_objects.common import DataType
from services.shared.v3_query_params import V3QueryParams


class SourcesQueryParams(V3QueryParams):
    source_region: Optional[str] = Field(default=None)
    data_source: Optional[str] = Field(default=None)
    source: Optional[str] = Field(default=None)

    @computed_field
    @cached_property
    def source_datatype(self) -> Optional[DataType]:
        return DataType(self.source) if self.source else None

    def _get_total_cache_dict(self) -> dict | None:
        key = super()._get_total_cache_dict()
        if key is None:
            return None

        key.update(
            {
                "source_region": self.source_region,
                "data_source": self.data_source,
                "source": self.source,
            }
        )
        return key
