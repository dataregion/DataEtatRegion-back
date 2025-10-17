from http import HTTPStatus
import inspect
from typing import Literal
from fastapi import Query
from fastapi.params import Query as QueryCls

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
        self.source_region = self._handle_default(source_region)
        self.data_source = self._handle_default(data_source)
        self.source = self._handle_default(source)
        self.source = DataType(self.source) if self.source is not None else None

    def _get_total_cache_dict(self) -> dict | None:
        key = super()._get_total_cache_dict()
        if key is None:
            return None
        
        key.update(
            {
                "source_region": self.source_region,
                "data_source": self.data_source,
                "source": self.source
            }
        )

        return key


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
        colonnes: str | None = Query(None, description="Liste des codes des colonnes à récupérer, séparés par des virgules"),
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
        self.niveau_geo = self._handle_default(niveau_geo)
        self.code_geo = self._split(code_geo)
        self.ref_qpv = self._handle_default(ref_qpv)
        self.code_qpv = self._split(code_qpv)
        self.theme = self._split(theme, "|")
        self.beneficiaire_code = self._split(beneficiaire_code)
        self.beneficiaire_categorieJuridique_type = self._split(beneficiaire_categorieJuridique_type)

        self.annee = self._handle_default(annee)
        self.annee = self._split(self.annee)
        self.annee = [int(a) for a in self.annee] if self.annee is not None else []

        self.centres_couts = self._split(centres_couts)
        self.domaine_fonctionnel = self._split(domaine_fonctionnel)
        self.referentiel_programmation = self._split(referentiel_programmation)
        self.tags = self._split(tags)
        self.grouping = self._split(grouping)
        self.grouped = self._split(grouped)

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

    def _get_total_cache_dict(self) -> dict | None:
        key = super()._get_total_cache_dict()
        if key is None:
            return None
        
        if (
            self.n_ej is not None or \
            self.code_programme is not None or\
            self.code_geo is not None or \
            self.niveau_geo is not None or \
            self.ref_qpv is not None or \
            self.code_qpv is not None or \
            self.beneficiaire_code is not None or \
            self.centres_couts is not None or \
            self.domaine_fonctionnel is not None or \
            self.search is not None or \
            self.is_group_request()
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
    def make_default() -> "FinancialLineQueryParams":
        defaults = _extract_query_defaults(FinancialLineQueryParams)
        default_inst = FinancialLineQueryParams(**defaults)
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
