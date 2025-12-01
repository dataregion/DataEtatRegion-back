from http import HTTPStatus
from typing import Optional

from pydantic import ConfigDict, Field, computed_field, model_validator

from models.exceptions import BadRequestError
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

        return self
