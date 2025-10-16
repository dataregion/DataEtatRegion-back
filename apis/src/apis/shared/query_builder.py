from http import HTTPStatus
from typing import Generic, Literal, TypeVar

from fastapi import Query
from sqlalchemy import Column, ColumnExpressionArgument, func, select, or_
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session, DeclarativeBase, load_only
from sqlalchemy.orm.attributes import InstrumentedAttribute

import logging

from apis.apps.budget.models.total import Total
from apis.shared.exceptions import BadRequestError


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
        return val.split(separator) if val else None


T = TypeVar("T", bound=DeclarativeBase)


class V3QueryBuilder(Generic[T]):
    def __init__(self, model: type[T], session: Session, params: V3QueryParams):
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self._model = model
        self._session = session
        self._params = params
        self._query = select(self._model)

        if self._params.colonnes is not None:
            selected_colonnes = [
                getattr(self._model, c) for c in self._params.colonnes if c in inspect(self._model).columns.keys()
            ]
            self.select_custom_model_properties(selected_colonnes)

    def select_custom_model_properties(self, colonnes: list):
        # XXX: On ne charge que les colonnes demandées
        # le raiseload empêche le lazy load des colonnes non demandées
        self._query = select(self._model).options(
            load_only(*colonnes, raiseload=True),
        )
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
        all = self._session.execute(self._query).unique().scalars().all()
        data = list(all)

        count_plus_one = len(data)
        data = data[: self._params.page_size]
        return data, self._params.page_size < count_plus_one

    def select_one(self):
        return self._session.execute(self._query).unique().scalar_one_or_none()
