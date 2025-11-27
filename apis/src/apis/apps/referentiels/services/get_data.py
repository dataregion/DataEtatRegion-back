from sqlalchemy import ColumnExpressionArgument
from sqlalchemy.orm import Session, DeclarativeBase

from services.query_builders.v3_query_params import V3QueryParams
from services.query_builders.v3_query_builder import V3QueryBuilder


def get_all_data(
    model: DeclarativeBase,
    db: Session,
    params: V3QueryParams,
    conditions: list[ColumnExpressionArgument[bool]] = [],
):
    builder = V3QueryBuilder(model, db, params).sort_by_params().search().paginate()
    for c in conditions:
        builder = builder.where_custom(c)
    return builder.select_all()


def get_one_data(
    model: DeclarativeBase,
    db: Session,
    params: V3QueryParams,
    conditions: list[ColumnExpressionArgument[bool]] = [],
):
    builder = V3QueryBuilder(model, db, params)
    for c in conditions:
        builder = builder.where_custom(c)
    return builder.select_one()
