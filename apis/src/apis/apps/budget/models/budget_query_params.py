from typing import Literal
from fastapi import Query

from models.value_objects.common import DataType

from apis.apps.budget.models.colonne import Colonne
from apis.shared.query_builder import V3QueryParams


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
        self.source_region = source_region
        self.data_source = data_source
        self.source = DataType(source) if source is not None else None


class FinancialLineQueryParams(SourcesQueryParams):

    def __init__(
        self,
        source_region: str | None = Query(None),
        data_source: str | None = Query(None),
        source: str | None = Query(None),
        n_ej: str | None = Query(None),
        code_programme: str | None = Query(None),
        niveau_geo: str | None = Query(None),
        code_geo: str | None = Query(None),
        ref_qpv: Literal[2015, 2024] | None = Query(None),
        code_qpv: str | None = Query(None),
        theme: str | None = Query(None),
        siret_beneficiaire: str | None = Query(None),
        types_beneficiaire: str | None = Query(None),
        annee: str | None = Query(None),
        centres_couts: str | None = Query(None),
        domaine_fonctionnel: str | None = Query(None),
        referentiel_programmation: str | None = Query(None),
        tags: str | None = Query(None),
        grouping: str | None = Query(None),
        grouped: str | None = Query(None),
        colonnes: str | None = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(100, ge=1, le=500),
        sort_by: str | None = Query(None),
        sort_order: Literal["asc", "desc"] | None = Query(None),
        search: str | None = Query(None),
        fields_search: str | None = Query(None),
    ):
        super().__init__(
            source_region,
            data_source,
            source,
            colonnes,
            page,
            page_size,
            sort_by,
            sort_order,
            search,
            fields_search,
        )
        self.n_ej = self._split(n_ej)
        self.code_programme = self._split(code_programme)
        self.niveau_geo = niveau_geo
        self.code_geo = self._split(code_geo)
        self.ref_qpv = ref_qpv
        self.code_qpv = self._split(code_qpv)
        self.theme = self._split(theme, "|")
        self.siret_beneficiaire = self._split(siret_beneficiaire)
        self.types_beneficiaire = self._split(types_beneficiaire)
        self.annee = self._split(annee)
        self.centres_couts = self._split(centres_couts)
        self.domaine_fonctionnel = self._split(domaine_fonctionnel)
        self.referentiel_programmation = self._split(referentiel_programmation)
        self.tags = self._split(tags)
        self.grouping = self._split(grouping)
        self.grouped = self._split(grouped)

        if bool(self.niveau_geo) ^ bool(self.code_geo):
            raise ValueError(
                "Les paramètres 'niveau_geo' et 'code_geo' doivent être fournis ensemble."
            )
        if bool(self.ref_qpv) ^ bool(self.code_qpv):
            raise ValueError(
                "Les paramètres 'ref_qpv' et 'code_qpv' doivent être fournis ensemble."
            )

    def map_colonnes(self, list_colonnes: list[Colonne]):
        casted = []
        for colonne in self.grouping:
            casted.append([x for x in list_colonnes if x.code == colonne][0])
        self.grouping = casted
