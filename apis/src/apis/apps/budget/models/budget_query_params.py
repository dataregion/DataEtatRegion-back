from http import HTTPStatus
import inspect
from typing import Literal
from fastapi import Query
from fastapi.params import Query as QueryCls

from apis.shared.colonne import Colonne
from apis.shared.exceptions import BadRequestError
from apis.shared.query_builder import FinancialLineQueryParams


class BudgetQueryParams(FinancialLineQueryParams):
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
        beneficiaire_code: str | None = Query(None, description="Siret du bénéficiaire"),
        beneficiaire_categorieJuridique_type: str | None = Query(
            None, description="Type de la catégorie juridique du bénéficiaire"
        ),
        annee: str | None = Query(None),
        centres_couts: str | None = Query(None),
        domaine_fonctionnel: str | None = Query(None),
        referentiel_programmation: str | None = Query(None),
        tags: str | None = Query(None),
        grouping: str | None = Query(None),
        grouped: str | None = Query(None),
        colonnes: str | None = Query(
            None, description="Liste des codes des colonnes à récupérer, séparés par des virgules"
        ),
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
            n_ej,
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
            domaine_fonctionnel,
            referentiel_programmation,
            colonnes,
            page,
            page_size,
            sort_by,
            sort_order,
            search,
            fields_search,
        )
        self.tags = self._split(tags)
        self.grouping = self._split(grouping)
        self.grouped = self._split(grouped)

    def is_group_request(self):
        """Indique si la requête est une requête de grouping."""
        len_grouping = len(self.grouping) if self.grouping is not None else 0
        len_grouped = len(self.grouped) if self.grouped is not None else 0

        return len_grouping != len_grouped

    def map_colonnes_grouping(self, list_colonnes: list[Colonne]):
        casted = []
        grouping = self.grouping or []
        for colonne in grouping:
            found = [x for x in list_colonnes if x.code == colonne]
            if len(found) == 0:
                raise BadRequestError(
                    code=HTTPStatus.BAD_REQUEST,
                    api_message=f"La colonne demandée '{colonne}' n'existe pas pour le grouping.",
                )
            casted.append(found[0])
        self.grouping = casted

    def _get_total_cache_dict(self) -> dict | None:
        key = super()._get_total_cache_dict()
        print(key)
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
            print("NO CACHE")
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
        defaults = _extract_query_defaults(BudgetQueryParams)
        default_inst = BudgetQueryParams(**defaults)
        return default_inst


def _extract_queries(cls) -> dict[str, QueryCls]:
    """
    Extrait les paramètres Query() définis dans le constructeur (__init__) d'une classe FastAPI.
    """
    sig = inspect.signature(cls.__init__)
    queries = {}
    for name, param in sig.parameters.items():
        # On ignore 'self'
        if name == "self":
            continue

        if isinstance(param.default, QueryCls):
            queries[name] = param.default
    return queries


def _extract_query_defaults(cls):
    """
    Extrait les valeurs par défaut de tous les paramètres Query()
    définis dans le constructeur (__init__) d'une classe FastAPI.
    """
    params = _extract_queries(cls)
    defaults = {name: param.default for name, param in params.items()}
    return defaults
