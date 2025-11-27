from typing import Literal

from fastapi import Query
from models.value_objects.common import DataType
from services.query_builders.v3_query_params import V3QueryParams


class SourcesQueryParams(V3QueryParams):
    def __init__(
        self,
        source_region: str | None = Query(None),
        data_source: str | None = Query(None),
        source: str | None = Query(None),
        colonnes: str | None = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(100, ge=1, le=500),
        sort_by: str | None = Query(None),
        sort_order: Literal["asc", "desc"] | None = Query(None),
        search: str | None = Query(None),
        fields_search: str | None = Query(None),
    ):
        super().__init__(
            colonnes, page, page_size, sort_by, sort_order, search, fields_search
        )
        self.source_region = self._handle_default(source_region)
        self.data_source = self._handle_default(data_source)
        self.source = self._handle_default(source)
        self.source = DataType(self.source) if self.source is not None else None

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
