from http import HTTPStatus
from logging import Logger
from apis.shared.query_builder import V3QueryParams
from fastapi import APIRouter, Depends
from marshmallow_sqlalchemy import SQLAlchemyAutoSchema
from sqlalchemy.orm import Session, DeclarativeBase
from typing import Type

from apis.apps.referentiels.services.get_data import get_all_data, get_one_data
from apis.database import get_session
from models.connected_user import ConnectedUser
from apis.exception_handlers import error_responses
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.shared.models import APISuccess


def create_referentiel_router(
    model: Type[DeclarativeBase],
    schema: SQLAlchemyAutoSchema,
    success_response: APISuccess,
    keycloak_validator: KeycloakTokenValidator,
    logger: Logger,
    model_name: str,
    code_column: str = "code",
    label_column: str = "label",
) -> APIRouter:
    router = APIRouter(prefix=f"/{model_name}", tags=[f"{model_name.capitalize()}"])

    @router.get(
        "",
        summary=f"Liste de tous les {model_name}",
        response_model=success_response,
        responses=error_responses(),
    )
    def list_all(
        params: V3QueryParams = Depends(),
        session: Session = Depends(get_session),
        user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
    ):
        logger.debug(f"[{model_name.upper()}] Récupération des {model_name}")

        data, has_next = get_all_data(model, session, params)
        if len(data) == 0:
            return APISuccess(
                code=HTTPStatus.NO_CONTENT,
                message="Aucun résultat ne correspond à vos critères de recherche",
                data=[],
            )

        return APISuccess(
            code=HTTPStatus.OK,
            message=f"Liste des {model_name}",
            data=schema(only=params.colonnes or schema._declared_fields.keys(), many=True).dump(data),
            has_next=has_next,
            current_page=params.page,
        )

    @router.get(
        "/{code}",
        summary=f"Get {model_name} by code",
        response_model=success_response,
        responses=error_responses(),
    )
    def get_by_code(
        code: str,
        params: V3QueryParams = Depends(),
        session: Session = Depends(get_session),
        user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
    ):
        logger.debug(f"[{model_name.upper()}] Récupération de {model_name} par {code_column} : {code}")

        data = get_one_data(model, session, params, [getattr(model, code_column) == code])
        if data is None:
            return APISuccess(
                code=HTTPStatus.NO_CONTENT,
                message="Aucun résultat ne correspond à vos critères de recherche",
                data=[],
            )
        data = [data]

        return APISuccess(
            code=HTTPStatus.OK,
            message=f"{model_name.capitalize()}[code={code}]",
            data=schema(only=params.colonnes or schema._declared_fields.keys(), many=True).dump(data),
        )

    return router
