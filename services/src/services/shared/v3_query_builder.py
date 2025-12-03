from typing import Annotated, Generic, Optional, TypeVar, Union, get_args, get_origin

from sqlalchemy import (
    Column,
    ColumnElement,
    ColumnExpressionArgument,
    Select,
    Sequence,
    func,
    select,
    or_,
)
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session, DeclarativeBase, load_only
from sqlalchemy.orm.attributes import InstrumentedAttribute

import logging

from models.value_objects.total import Total
from services.shared.v3_query_params import V3QueryParams
from services.utilities.observability import summary_of_time


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

        if self._params.colonnes_list is not None:
            selected_colonnes = [
                getattr(self._model, c) for c in self._params.colonnes_list if c in inspect(self._model).columns.keys()
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
                (func.coalesce(func.count(model.id), 0).label("total")),  # type: ignore
                (func.coalesce(func.sum(model.montant_ae), 0).label("total_montant_engage")),  # type: ignore
                (func.coalesce(func.sum(model.montant_cp), 0).label("total_montant_paye")),  # type: ignore
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
