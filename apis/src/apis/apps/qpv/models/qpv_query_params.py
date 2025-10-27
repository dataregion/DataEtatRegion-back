from http import HTTPStatus
from typing import Literal
from fastapi import Query

from models.value_objects.common import DataType

from apis.apps.budget.models.colonne import Colonne
from apis.shared.exceptions import BadRequestError
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
        super().__init__(colonnes, page, page_size, sort_by, sort_order, search, fields_search)
        self.source_region = source_region
        self.data_source = data_source
        self.source = DataType(source) if source is not None else None


class QpvQueryParams(SourcesQueryParams):
    def __init__(
        self,
        source_region: str | None = Query(None),
        data_source: str | None = Query(None),
        source: str | None = Query(None),
        code_programme: str | None = Query(None),
        not_code_programme: str | None = Query(None),
        annee: str | None = Query(None),
        niveau_geo: str | None = Query(None),
        code_geo: str | None = Query(None),
        ref_qpv: Literal["2015", "2024"] | None = Query(None),
        code_qpv: str | None = Query(None),
        theme: str | None = Query(None),
        beneficiaire_code: str | None = Query(None, description="Siret du bénéficiaire"),
        beneficiaire_categorieJuridique_type: str | None = Query(
            None, description="Type de la catégorie juridique du bénéficiaire"
        ),
        centres_couts: str | None = Query(None),
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
        self.code_programme = self._split(code_programme)
        self.not_code_programme = self._split(not_code_programme)
        self.niveau_geo = niveau_geo
        self.code_geo = self._split(code_geo)
        self.ref_qpv = ref_qpv
        self.code_qpv = self._split(code_qpv)
        self.theme = self._split(theme, "|")
        self.beneficiaire_code = self._split(beneficiaire_code)
        self.beneficiaire_categorieJuridique_type = self._split(beneficiaire_categorieJuridique_type)
        self.annee = [int(a) for a in self._split(annee)] if annee is not None else []
        self.centres_couts = self._split(centres_couts)

        if bool(self.niveau_geo) ^ bool(self.code_geo):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Les paramètres 'niveau_geo' et 'code_geo' doivent être fournis ensemble.",
            )

    def map_colonnes_tableau(self, list_colonnes: list[Colonne]):
        casted = []
        colonnes = self.colonnes or []
        for colonne in colonnes:
            found = [x for x in list_colonnes if x.code == colonne]
            if len(found) == 0:
                raise BadRequestError(
                    code=HTTPStatus.BAD_REQUEST,
                    api_message=f"La colonne demandée '{colonne}' n'existe pas pour le tableau.",
                )
            casted.append(found[0])
        self.colonnes = casted
