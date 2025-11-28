from functools import cached_property
from http import HTTPStatus
from typing import Optional

from pydantic import Field, computed_field, model_validator

from models.exceptions import BadRequestError
from services.qpv.colonnes import get_list_colonnes_tableau
from services.shared.financial_line_query_builder import FinancialLineQueryParams


class QpvQueryParams(FinancialLineQueryParams):
    not_code_programme: Optional[str] = Field(default=None)

    @computed_field
    @cached_property
    def not_code_programme_list(self) -> float:
        return self._split(self.not_code_programme)

    @model_validator(mode="after")
    def finalize_qpv(self):
        if bool(self.niveau_geo) ^ bool(self.code_geo):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Les paramètres 'niveau_geo' et 'code_geo' doivent être fournis ensemble.",
            )

        self._check_colonnes(get_list_colonnes_tableau())

        return self
