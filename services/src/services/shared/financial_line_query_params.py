from typing import List, Literal, Optional

from pydantic import ConfigDict, Field, computed_field
from services.shared.source_query_params import SourcesQueryParams


class FinancialLineQueryParams(SourcesQueryParams):
    model_config = ConfigDict(frozen=True)

    code_programme: Optional[str] = Field(default=None)
    niveau_geo: Optional[str] = Field(default=None)
    code_geo: Optional[str] = Field(default=None)
    ref_qpv: Optional[Literal["2015", "2024"]] = Field(default=None)
    code_qpv: Optional[str] = Field(default=None)
    theme: Optional[str] = Field(default=None)
    beneficiaire_code: Optional[str] = Field(default=None)
    beneficiaire_categorieJuridique_type: Optional[str] = Field(default=None)
    annee: Optional[str] = Field(default=None)
    centres_couts: Optional[str] = Field(default=None)

    @computed_field
    def code_programme_list(self) -> Optional[List[str]]:
        return self._split(self.code_programme)

    @computed_field
    def code_geo_list(self) -> Optional[List[str]]:
        return self._split(self.code_geo)

    @computed_field
    def code_qpv_list(self) -> Optional[List[str]]:
        return self._split(self.code_qpv)

    @computed_field
    def theme_list(self) -> Optional[List[str]]:
        return self._split(self.theme, "|")

    @computed_field
    def beneficiaire_code_list(self) -> Optional[List[str]]:
        return self._split(self.beneficiaire_code)

    @computed_field
    def beneficiaire_categorieJuridique_type_list(self) -> Optional[List[str]]:
        return self._split(self.beneficiaire_categorieJuridique_type)

    @computed_field
    def annee_list(self) -> Optional[List[int]]:
        lst = self._split(self.annee) if self.annee else None
        return [int(x) for x in lst] if lst else None

    @computed_field
    def centres_couts_list(self) -> Optional[List[str]]:
        return self._split(self.centres_couts)

    @staticmethod
    def make_default() -> "FinancialLineQueryParams":
        return FinancialLineQueryParams()
