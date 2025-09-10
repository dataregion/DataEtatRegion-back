from http import HTTPStatus
import logging
from fastapi import Depends
from fastapi.responses import JSONResponse
from requests import Session

from models.entities.refs.Qpv import Qpv
from models.schemas.refs import QpvSchema

from apis.apps.budget.models.budget_query_params import V3QueryParams
from apis.apps.referentiels.services.get_data import get_all_data
from apis.apps.referentiels.services.referentiels_router_factory import (
    create_referentiel_router,
)
from apis.database import get_session
from models.connected_user import ConnectedUser
from apis.exception_handlers import error_responses
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.shared.models import APISuccess


logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()
router = create_referentiel_router(Qpv, QpvSchema, keycloak_validator, logger, "qpv")


@router.get(
    "/{annee}",
    summary="Find all QPV by annee",
    response_class=JSONResponse,
    responses=error_responses(),
)
def find_all_by_annee_decoupage(
    annee: str,
    params: V3QueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    if annee != "2015" and annee != "2024":
        raise ValueError("L'année de découpage renseignée est erronée.")

    logger.debug(f"[QPV] Récupération des qpv de l'année de découpage {annee}")
    data, has_next = get_all_data(Qpv, session, params, [Qpv.annee_decoupage == int(annee)])
    if len(data) == 0:
        return APISuccess(
            code=HTTPStatus.NO_CONTENT,
            message="Aucun résultat ne correspond à vos critères de recherche",
            data=[],
        )

    return APISuccess(
        code=HTTPStatus.OK,
        message=f"Liste des QPV de l'année de découpage {annee}",
        data=QpvSchema(many=True).dump(data),
        current_page=params.page,
        has_next=has_next,
    )
