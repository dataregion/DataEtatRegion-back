from http import HTTPStatus
from typing import Optional

from pydantic import ConfigDict, Field, computed_field, model_validator

from models.exceptions import BadRequestError
from services.qpv.colonnes import get_list_colonnes_tableau
from services.shared.financial_line_query_builder import FinancialLineQueryParams


class QpvQueryParams(FinancialLineQueryParams):
    model_config = ConfigDict(frozen=True)

    not_code_programme: Optional[str] = Field(default=None)

    @computed_field
    def not_code_programme_list(self) -> float:
        return self._split(self.not_code_programme)

    @model_validator(mode="after")
    def post_init_qpv(self):
        if bool(self.niveau_geo) ^ bool(self.code_geo):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Les paramètres 'niveau_geo' et 'code_geo' doivent être fournis ensemble.",
            )

        if self.sort_by is not None and self.sort_by not in [x.code for x in get_list_colonnes_tableau()]:
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message=f"La colonne demandée '{self.sort_by}' n'existe pas pour le tri.",
            )

        codes = self._split(self.fields_search) if self.fields_search else []
        if codes is not None and not all(field in [x.code for x in get_list_colonnes_tableau()] for field in codes):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message=f"Les colonnes demandées '{self.fields_search}' n'existe pas pour la recherche.",
            )

        codes = self._split(self.colonnes) if self.colonnes else []
        for code in codes:
            found = [x for x in get_list_colonnes_tableau() if x.code == code]
            if len(found) == 0:
                raise BadRequestError(
                    code=HTTPStatus.BAD_REQUEST,
                    api_message=f"La colonne demandée '{code}' n'existe pas pour le tableau.",
                )

        return self
