from http import HTTPStatus
from typing import Literal
from fastapi import Query

from apis.shared.exceptions import BadRequestError
from services.query_builders.financial_line_query_builder import FinancialLineQueryParams


class QpvQueryParams(FinancialLineQueryParams):
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
            code_programme,
            niveau_geo,
            code_geo,
            ref_qpv,
            code_qpv,
            theme,
            beneficiaire_code,
            beneficiaire_categorieJuridique_type,
            annee,
            centres_couts,
            colonnes,
            page,
            page_size,
            sort_by,
            sort_order,
            search,
            fields_search,
        )
        self.not_code_programme = self._split(not_code_programme)

        if bool(self.niveau_geo) ^ bool(self.code_geo):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Les paramètres 'niveau_geo' et 'code_geo' doivent être fournis ensemble.",
            )
