from typing import Literal

from fastapi import Query
from sqlalchemy import Column, ColumnExpressionArgument, select, or_
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import InstrumentedAttribute

import logging


class V3QueryParams:
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
        self.page = page
        self.page_size = page_size
        self.sort_by = sort_by
        self.sort_order = sort_order
        self.search = search
        self.fields_search = self._split(fields_search)

    def _split(self, val: str | None, separator: str = ",") -> list | None:
        return val.split(separator) if val else None


class V3QueryBuilder:

    def __init__(self, model, session: Session, params: V3QueryParams):
        self._model = model
        self._session = session
        self._params = params
        self._query = select(self._model)
        self._select_model = True
        
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

        if self._params.colonnes is not None:
            selected_colonnes = [
                getattr(self._model, c)
                for c in self._params.colonnes
                if c in inspect(self._model).columns.keys()
            ]
            self.select_custom_colonnes(selected_colonnes)

    def select_custom_colonnes(self, colonnes: list):
        self._query = select(*colonnes)
        self._select_model = False
        return self

    def where_custom(self, where: ColumnExpressionArgument[bool]):
        self._query = self._query.where(where)
        return self._query

    def where_field_is(self, colonne: Column, value: dict, can_be_null=False):
        if value is None:
            return

        complete_cond = [
            (
                colonne == value["type"](value["value"])
                if "type" in value
                else value["value"]
            )
        ]
        if can_be_null:
            complete_cond.append(colonne.is_(None))

        self._query = self._query.where(or_(*complete_cond))
        return self

    def where_field_in(
        self, colonne: Column, set_of_values: list | None, can_be_null=False
    ):
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

    def sort_by_params(self):
        if self._params.sort_by is not None:
            sortby_colonne = getattr(self._model, self._params.sort_by, None)
            if isinstance(sortby_colonne, InstrumentedAttribute):
                direction = self._params.sort_order or "asc"
                self._query = self._query.order_by(
                    sortby_colonne.asc()
                    if direction == "asc"
                    else sortby_colonne.desc()
                )
        return self

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

    def select_all(self):
        data = []
        if self._select_model:
            data = list(self._session.execute(self._query).unique().scalars().all())
        else:
            data = list(self._session.execute(self._query).mappings().all())

        count_plus_one = len(data)
        data = data[: self._params.page_size]
        return data, self._params.page_size < count_plus_one

    def select_one(self):
        return self._session.execute(self._query).unique().scalar_one_or_none()
