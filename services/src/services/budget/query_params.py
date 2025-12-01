from http import HTTPStatus
from typing import List, Optional
from pydantic import ConfigDict, Field, computed_field, model_validator

from models.exceptions import BadRequestError
from models.value_objects.colonne import Colonne
from services.budget.colonnes import get_list_colonnes_grouping
from services.shared.financial_line_query_builder import (
    FinancialLineQueryParams,
)


class BudgetQueryParams(FinancialLineQueryParams):
    model_config = ConfigDict(frozen=True)

    n_ej: Optional[str] = Field(default=None)
    domaine_fonctionnel: Optional[str] = Field(default=None)
    referentiel_programmation: Optional[str] = Field(default=None)
    tags: Optional[str] = Field(default=None)
    grouping: Optional[str] = Field(default=None)
    grouped: Optional[str] = Field(default=None)

    @computed_field
    def n_ej_list(self) -> float:
        return self._split(self.n_ej)

    @computed_field
    def domaine_fonctionnel_list(self) -> float:
        return self._split(self.domaine_fonctionnel)

    @computed_field
    def referentiel_programmation_list(self) -> float:
        return self._split(self.referentiel_programmation)

    @computed_field
    def tags_list(self) -> float:
        return self._split(self.tags)

    @computed_field
    def grouping_list(self) -> Optional[List[Colonne]]:
        casted = []
        codes = self._split(self.grouping) if self.grouping else []
        for code in codes:
            found = [x for x in get_list_colonnes_grouping() if x.code == code]
            if len(found) == 0:
                raise BadRequestError(
                    code=HTTPStatus.BAD_REQUEST,
                    api_message=f"La colonne demandée '{code}' n'existe pas pour le grouping.",
                )
            casted.append(found[0])
        return casted if len(casted) > 0 else None

    @computed_field
    def grouped_list(self) -> float:
        return self._split(self.grouped)

    @model_validator(mode="after")
    def post_init_budget(self):
        if bool(self.niveau_geo) ^ bool(self.code_geo):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Les paramètres 'niveau_geo' et 'code_geo' doivent être fournis ensemble.",
            )
        if bool(self.ref_qpv) ^ bool(self.code_qpv):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Les paramètres 'ref_qpv' et 'code_qpv' doivent être fournis ensemble.",
            )

        if self.grouping_list is not None:
            # Check la validité de la paire grouping et grouped
            if self.grouped_list is None and len(self.grouping_list) > 1:
                raise BadRequestError(
                    code=HTTPStatus.BAD_REQUEST,
                    api_message="Mauvaise utilisation des paramètres de grouping",
                )
            if self.grouped_list is not None and len(self.grouping_list) not in (
                len(self.grouped_list) + 1,
                len(self.grouped_list),
            ):
                raise BadRequestError(
                    code=HTTPStatus.BAD_REQUEST,
                    api_message="Mauvaise utilisation des paramètres de grouping",
                )

        return self

    def is_group_request(self):
        """Indique si la requête est une requête de grouping."""
        len_grouping = len(self.grouping_list) if self.grouping_list is not None else 0
        len_grouped = len(self.grouped_list) if self.grouped_list is not None else 0
        return len_grouping != len_grouped

    def _get_total_cache_dict(self) -> dict | None:
        key = super()._get_total_cache_dict()
        if key is None:
            return None

        if (
            self.n_ej is not None
            or self.code_programme is not None
            or self.code_geo is not None
            or self.niveau_geo is not None
            or self.ref_qpv is not None
            or self.code_qpv is not None
            or self.beneficiaire_code is not None
            or self.centres_couts is not None
            or self.domaine_fonctionnel is not None
            or self.search is not None
            or self.is_group_request()
        ):
            # La requête ne doit pas être mise en cache
            return None

        key.update(
            {
                "theme": self.theme,
                "beneficiaire_categorieJuridique_type": self.beneficiaire_categorieJuridique_type,
                "annee": self.annee,
                "referentiel_programmation": self.referentiel_programmation,
                "tags": self.tags,
                "grouping": self.grouping,
                "grouped": self.grouped,
            }
        )

        return key

    @staticmethod
    def make_default() -> "BudgetQueryParams":
        return BudgetQueryParams()
