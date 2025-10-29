from http import HTTPStatus
from typing import Generic, Literal, Optional, TypeVar, Union

from fastapi import Query
from fastapi.params import Query as QueryCls
from sqlalchemy import Column, ColumnElement, ColumnExpressionArgument, Select, Sequence, func, select, or_
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session, DeclarativeBase, load_only
from sqlalchemy.orm.attributes import InstrumentedAttribute

import logging

from apis.apps.budget.models.total import Total
from apis.shared.exceptions import BadRequestError
from abc import ABC, abstractmethod


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
        if is_grouping:
            self._query = select(*colonnes).select_from(self._model)
            self._is_grouping = True
        else:
            # XXX: On ne charge que les colonnes demandées
            # le raiseload empêche le lazy load des colonnes non demandées
            self._query = select(self._model).options(load_only(*colonnes, raiseload=True))
        return self

    def where_custom(self, where: ColumnExpressionArgument[bool]):
        self._query = self._query.where(where)
        return self._query

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

    def get_total(self, type: str):
        unpaginated = self._query.limit(None).offset(None).subquery()
        totals_query = select(
            (
                func.coalesce(func.sum(unpaginated.c.total), 0).label("total")
                if type == "groupings"
                else func.coalesce(func.count(unpaginated.c.id), 0).label("total")
            ),
            (
                func.coalesce(func.sum(unpaginated.c.total_montant_engage), 0).label("total_montant_engage")
                if type == "groupings"
                else func.coalesce(func.sum(unpaginated.c.montant_ae), 0).label("total_montant_engage")
            ),
            (
                func.coalesce(func.sum(unpaginated.c.total_montant_paye), 0).label("total_montant_paye")
                if type == "groupings"
                else func.coalesce(func.sum(unpaginated.c.montant_cp), 0).label("total_montant_paye")
            ),
        )
        result = self._session.execute(totals_query).one()
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
