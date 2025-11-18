from http import HTTPStatus
from typing import Annotated, Generic, Literal, Optional, TypeVar, Union, get_args, get_origin

from apis.shared.colonne import Colonnes
from fastapi import Query
from fastapi.params import Query as QueryCls
from models.value_objects.common import DataType
from sqlalchemy import Column, ColumnElement, ColumnExpressionArgument, Select, Sequence, func, select, or_
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session, DeclarativeBase, load_only
from sqlalchemy.orm.attributes import InstrumentedAttribute

import logging

from apis.apps.budget.models.total import Total
from apis.shared.exceptions import BadRequestError
from abc import ABC, abstractmethod

from services.utilities.observability import summary_of_time


class CacheableTotalQuery(ABC):
    """Classe abstraite pour les requêtes qui peuvent être mises en cache"""

    @abstractmethod
    def _get_total_cache_dict(self) -> dict | None:
        """
        Retourne une clé de cache sous forme de dictionnaire ou None si la requête de totaux ne doit pas être mise en cache.

        Returns:
            dict | None: Dictionnaire représentant la clé de cache ou None
        """
        pass

    def get_total_cache_key(self) -> frozenset | None:
        cache_dict = self._get_total_cache_dict()
        if cache_dict is None:
            return None

        # Convertir les valeurs non-hashables en tuples
        hashable_items = []
        for key, value in cache_dict.items():
            if isinstance(value, list):
                if value is not None:
                    # Gérer les listes d'objets non-hashables
                    hashable_list = []
                    for item in value:
                        if hasattr(item, "code"):
                            hashable_list.append(item.code)
                        elif hasattr(item, "__dict__"):  # Objet standard avec attributs
                            hashable_list.append(frozenset(item.__dict__.items()))
                        else:
                            hashable_list.append(str(item))  # Fallback en string
                    hashable_items.append((key, tuple(hashable_list)))
                else:
                    hashable_items.append((key, None))
            else:
                hashable_items.append((key, value))

        return frozenset(hashable_items)


class V3QueryParams(CacheableTotalQuery):
    def __init__(
        self,
        colonnes: str | None = Query(None),
        page: int = Query(1, ge=1),
        page_size: int = Query(100, ge=1, le=1000),
        sort_by: str | None = Query(None),
        sort_order: Literal["asc", "desc"] | None = Query(None),
        search: str | None = Query(None),
        fields_search: str | None = Query(None),
    ):
        self.colonnes = self._split(colonnes)
        self.page = self._handle_default(page)
        self.page_size = self._handle_default(page_size)
        self.sort_by = self._handle_default(sort_by)
        self.sort_order = self._handle_default(sort_order)
        self.search = self._handle_default(search)
        self.fields_search = self._split(fields_search)

        if bool(self.sort_by) ^ bool(self.sort_order):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Les paramètres 'sort_by' et 'sort_order' doivent être fournis ensemble.",
            )
        if bool(self.search) ^ bool(self.fields_search):
            raise BadRequestError(
                code=HTTPStatus.BAD_REQUEST,
                api_message="Les paramètres 'search' et 'fields_search' doivent être fournis ensemble.",
            )

    def _split(self, val: str | None, separator: str = ",") -> list | None:
        val = self._handle_default(val)
        return val.split(separator) if val else None

    def _get_total_cache_dict(self) -> dict | None:
        return {
            "search": self.search,
            "fields_search": self.fields_search,
        }

    def _handle_default(self, val):
        if isinstance(val, QueryCls):
            return val.default
        return val


T = TypeVar("T", bound=DeclarativeBase)

SelectionType = Optional[
    Union[
        InstrumentedAttribute,  # ORM column attributes
        ColumnElement,  # SQL expressions (func.sum, etc.)
        Sequence[Union[InstrumentedAttribute, ColumnElement]],  # list/tuple of them
    ]
]


class V3QueryBuilder(Generic[T]):
    def __init__(self, model: type[T], session: Session, params: V3QueryParams):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._model = model
        if get_origin(model) is Annotated:
            self._model = get_args(model)[0]
        self._session = session
        self._params = params
        self._query = select(self._model)
        self._is_grouping = False
        """Représente si le builder qui est en train de build est une aggregation"""

        if self._params.colonnes is not None:
            selected_colonnes = [
                getattr(self._model, c) for c in self._params.colonnes if c in inspect(self._model).columns.keys()
            ]
            self.select_custom_model_properties(selected_colonnes)

    def select_custom_model_properties(self, colonnes: list, is_grouping: bool = False):
        if is_grouping or any(not hasattr(c, "property") for c in colonnes):
            self._query = select(*colonnes).select_from(self._model)
            self._is_grouping = True
        else:
            # XXX: On ne charge que les colonnes demandées
            # le raiseload empêche le lazy load des colonnes non demandées
            self._query = select(self._model).options(load_only(*colonnes, raiseload=True))
        return self

    def where_custom(self, where: ColumnExpressionArgument[bool]):
        self._query = self._query.where(where)
        return self

    def where_field_is(self, colonne: Column, value: dict, can_be_null=False):
        if value is None:
            return

        complete_cond = []
        if value["value"] is not None:
            complete_cond.append(colonne == value["type"](value["value"]) if "type" in value else value["value"])
        if can_be_null or value["value"] is None:
            complete_cond.append(colonne.is_(None))

        self._query = self._query.where(or_(*complete_cond))
        return self

    def where_field_in(self, colonne: Column, set_of_values: list | None, can_be_null=False):
        if set_of_values is None:
            return

        pruned = [x for x in set_of_values if x is not None]
        if len(pruned) == 0:
            return

        complete_cond = [colonne.in_(pruned)]
        if can_be_null:
            complete_cond.append(colonne.is_(None))

        self._query = self._query.where(or_(*complete_cond))
        return self

    def where_field_not_in(self, colonne: Column, set_of_values: list | None, can_be_null=False):
        if set_of_values is None:
            return

        pruned = [x for x in set_of_values if x is not None]
        if len(pruned) == 0:
            return

        complete_cond = [~colonne.in_(pruned)]
        if can_be_null:
            complete_cond.append(colonne.is_(None))

        self._query = self._query.where(or_(*complete_cond))
        return self

    def _get_model_id_colonne(self) -> InstrumentedAttribute:
        assert hasattr(self._model, "id") and isinstance(self._model.id, InstrumentedAttribute)  # type: ignore
        return self._model.id  # type: ignore

    def sort_by_params(self):
        if self._params.sort_by is not None:
            sortby_colonne = getattr(self._model, self._params.sort_by, None)
            if isinstance(sortby_colonne, InstrumentedAttribute):
                direction = self._params.sort_order or "asc"
                self._query = self._query.order_by(
                    sortby_colonne.asc() if direction == "asc" else sortby_colonne.desc()
                )
        # On finit toujours par in sort by id ASC après les sort utilisateur
        if not self.is_an_aggregation:
            id_attr = self._get_model_id_colonne()
            _sort_clause = id_attr.asc()  # type: ignore
            self._query = self._query.order_by(_sort_clause)
        return self

    @property
    def is_an_aggregation(self):
        """Représente si la requête qui est en train de build est une aggregation"""
        return hasattr(self._params, "grouping") and getattr(self._params, "grouping") is not None

    def search(self):
        if self._params.fields_search is not None:
            filters = []
            for field in self._params.fields_search:
                column = getattr(self._model, field, None)
                if isinstance(column, InstrumentedAttribute):
                    filters.append(column.ilike(f"%{self._params.search}%"))
            if filters:
                self._query = self._query.filter(or_(*filters))
        return self

    def paginate(self):
        self._logger.debug("paginate")
        offset = (self._params.page - 1) * self._params.page_size
        self._query = self._query.offset(offset).limit(self._params.page_size + 1)
        return self

    @summary_of_time()
    def get_total(self, _: str):
        model = self._model
        q = (
            select(
                (func.coalesce(func.count(model.id), 0).label("total")), # type: ignore
                (func.coalesce(func.sum(model.montant_ae), 0).label("total_montant_engage")), # type: ignore
                (func.coalesce(func.sum(model.montant_cp), 0).label("total_montant_paye")), # type: ignore
            )
            .select_from(model)
            .where(*self._query._where_criteria)
            .group_by(None)
            .order_by(None)
            .limit(None)
            .offset(None)
        )
        
        result = self._session.execute(q).one()
        return Total(
            total=result.total,
            total_montant_engage=result.total_montant_engage,
            total_montant_paye=result.total_montant_paye,
        )

    def select_all(self):
        if self._is_grouping:
            all = self._session.execute(self._query).mappings().all()
        else:
            all = self._session.execute(self._query).unique().scalars().all()
        data = list(all)

        count_plus_one = len(data)
        data = data[: self._params.page_size]
        return data, self._params.page_size < count_plus_one

    def select_one(self):
        return self._session.execute(self._query).unique().scalar_one_or_none()

    def with_selection(self, selection: SelectionType) -> "V3QueryBuilder[T]":
        """
        Replace the SELECT clause while keeping WHERE, GROUP BY, ORDER BY, etc.
        """
        # Prepare the base select list
        if isinstance(selection, (list, tuple)):
            new_query = select(*selection)
        elif isinstance(selection, Select):
            new_query = selection
        else:
            new_query = select(selection)

        # Re-apply FROM and all clauses from current query
        new_query = (
            new_query.select_from(self._query.get_final_froms()[0])
            .where(*self._query._where_criteria)
            .group_by(*self._query._group_by_clauses)
            .order_by(*self._query._order_by_clauses)
            .limit(self._query._limit)
            .offset(self._query._offset)
        )

        self._query = new_query
        self._select_model = False
        return self


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

        key.update({"source_region": self.source_region, "data_source": self.data_source, "source": self.source})

        return key


class SourcesQueryBuilder(V3QueryBuilder):
    def __init__(self, model: type[DeclarativeBase], session: Session, params: SourcesQueryParams) -> None:
        super().__init__(model, session, params)

    def source_is(self, source: DataType | str | None = None):
        if source is not None:
            self._query = self._query.where(self._model.source == source)
        return self

    def source_region_in(self, source_region: list[str] | None, can_be_null: bool = True):
        """Filtre sur la source region. Notons que ce filtre est passant sur les lignes sans source regions"""
        self.where_field_in(self._model.source_region, source_region, can_be_null=can_be_null)
        return self

    def data_source_is(self, data_source: str | None = None):
        self.where_field_in(self._model.data_source, [data_source], can_be_null=True)
        return self

    def par_identifiant_technique(self, source: DataType, id: int):
        """Filtre selon l'identifiant technique. ie couple source - id"""
        self._query = self._query.where(self._model.source == str(source.value), self._model.id == id)
        return self


class FinancialLineQueryParams(SourcesQueryParams):
    def __init__(
        self,
        source_region: str | None = Query(None),
        data_source: str | None = Query(None),
        source: str | None = Query(None),
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
            colonnes,
            page,
            page_size,
            sort_by,
            sort_order,
            search,
            fields_search,
        )
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

    def map_colonnes_tableau(self, list_colonnes: Colonnes):
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


class FinancialLineQueryBuilder(SourcesQueryBuilder):
    """
    Constructeur de requête SQLAlchemy pour la vue budget
    """

    def __init__(self, model: type[DeclarativeBase], session: Session, params: FinancialLineQueryParams) -> None:
        super().__init__(model, session, params)

    """
    Méthodes de création de conditions
    """

    def n_ej_in(self, n_ej: list[str] | None = None):
        self.where_field_in(self._model.n_ej, n_ej)
        return self

    def themes_in(self, themes: list[str] | None = None):
        self.where_field_in(self._model.programme_theme, themes)
        return self

    def code_programme_in(self, codes_programme: list[str] | None = None):
        self.where_field_in(self._model.programme_code, codes_programme)
        return self

    def code_programme_not_in(self, codes_programme: list[str] | None = None):
        self.where_field_not_in(self._model.programme_code, codes_programme)
        return self

    def beneficiaire_siret_in(self, sirets: list[str] | None = None):
        self.where_field_in(self._model.beneficiaire_code, sirets)
        return self

    def annee_in(self, annees: list[int] | None):
        self.where_field_in(self._model.annee, annees)
        return self

    def centres_couts_in(self, centres_couts: list[str] | None):
        self.where_field_in(self._model.centreCouts_code, centres_couts)
        return self

    def domaine_fonctionnel_in(self, dfs: list[str] | None):
        self.where_field_in(self._model.domaineFonctionnel_code, dfs)
        return self

    def referentiel_programmation_in(self, ref_prog: list[str] | None):
        self.where_field_in(self._model.referentielProgrammation_code, ref_prog)
        return self

    def categorie_juridique_in(
        self,
        types_beneficiaires: list[str] | None,
        includes_none: bool = False,
    ):
        conds = []
        if types_beneficiaires is not None and includes_none:
            conds.append(self._model.beneficiaire_categorieJuridique_type)

        if types_beneficiaires is not None:
            conds.append(self._model.beneficiaire_categorieJuridique_type.in_(types_beneficiaires))

        cond = or_(*conds)
        self._query = self._query.where(cond)
        return self

    def ej(self, ej: str, poste_ej: int):
        self._stmt = self._query.where(self._model.n_ej == ej).where(self._model.n_poste_ej == poste_ej)
        return self
