from sqlalchemy.orm import Session, DeclarativeBase

from models.value_objects.common import DataType
from services.query_builders.v3_query_builder import V3QueryBuilder
from services.query_builders.source_query_params import SourcesQueryParams


class SourcesQueryBuilder(V3QueryBuilder):
    def __init__(
        self, model: type[DeclarativeBase], session: Session, params: SourcesQueryParams
    ) -> None:
        super().__init__(model, session, params)

    def source_is(self, source: DataType | str | None = None):
        if source is not None:
            self._query = self._query.where(self._model.source == source)
        return self

    def source_region_in(
        self, source_region: list[str] | None, can_be_null: bool = True
    ):
        """Filtre sur la source region. Notons que ce filtre est passant sur les lignes sans source regions"""
        self.where_field_in(
            self._model.source_region, source_region, can_be_null=can_be_null
        )
        return self

    def data_source_is(self, data_source: str | None = None):
        self.where_field_in(self._model.data_source, [data_source], can_be_null=True)
        return self

    def par_identifiant_technique(self, source: DataType, id: int):
        """Filtre selon l'identifiant technique. ie couple source - id"""
        self._query = self._query.where(
            self._model.source == str(source.value), self._model.id == id
        )
        return self
