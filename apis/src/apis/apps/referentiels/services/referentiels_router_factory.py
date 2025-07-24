from http import HTTPStatus
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.orm import Session, DeclarativeBase
from typing import Type

from apis.apps.budget.models.budget_query_params import V3QueryParams
from apis.database import get_db
from apis.security import ConnectedUser, get_connected_user
from apis.shared.decorators import handle_exceptions
from apis.shared.models import APISuccess
from apis.shared.query_builder import V3QueryBuilder

def create_referentiel_router(
    model: Type[DeclarativeBase],
    schema: SQLAlchemyAutoSchema,
    model_name: str,
    code_column: str = "code",
    label_column: str = "label",
) -> APIRouter:
    
    router = APIRouter(prefix=f"/{model_name}", tags=[f"{model_name.capitalize()}"])

    @router.get("", summary=f"Liste de tous les {model_name}", response_class=JSONResponse)
    @handle_exceptions
    def list_all(params: V3QueryParams = Depends(), db: Session = Depends(get_db), user: ConnectedUser = Depends(get_connected_user)):
        builder = (
            V3QueryBuilder(model, db, params)
            .sort_by_params()
            .search()
            .paginate()
        )

        data, has_next = builder.select_all()
        if len(data) == 0:
            return APISuccess(
                code=HTTPStatus.NO_CONTENT,
                message="Aucun résultat ne correspond à vos critères de recherche",
                data=[],
            ).to_json_response()
        
        return APISuccess(
            code=HTTPStatus.OK,
            message=f"Liste des {model_name}",
            data=schema(many=True).dump(data),
            has_next=has_next,
            current_page=params.page
        ).to_json_response()


    @router.get("/{code}", summary=f"Get {model_name} by code", response_class=JSONResponse)
    @handle_exceptions
    def get_by_code(code: str, params: V3QueryParams = Depends(), db: Session = Depends(get_db), user: ConnectedUser = Depends(get_connected_user)):
        colonne = getattr(model, code_column)
        builder = (
            V3QueryBuilder(model, db, params)
            .where_field_is(colonne, code)
        )
        data = builder.select_one()
        if data is None:
            return APISuccess(
                code=HTTPStatus.NO_CONTENT,
                message="Aucun résultat ne correspond à vos critères de recherche",
                data=[],
            ).to_json_response()
        
        return APISuccess(
            code=HTTPStatus.OK,
            message=f"{model_name.capitalize()}[code={code}]",
            data=schema(many=False).dump(data)
        ).to_json_response()

    return router
