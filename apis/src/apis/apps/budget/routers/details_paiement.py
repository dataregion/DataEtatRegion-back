import logging
from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from apis.apps.budget.services.get_data import get_ligne
from apis.apps.budget.routers.api_models import DetailsPaiement
from apis.apps.budget.routers.shared import enforce_query_params_with_connected_user_rights
from apis.database import get_session_main
from apis.exception_handlers import error_responses
from apis.security.keycloak_token_validator import KeycloakTokenValidator

from sqlalchemy.orm import Session
from sqlalchemy import select
from models.connected_user import ConnectedUser
from models.entities.financial.FinancialCp import FinancialCp

from services.shared.source_query_params import SourcesQueryParams

from apis.shared.models import APISuccess

from models.value_objects.common import DataType

router = APIRouter()
logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()


# Models
class InnerDetailsPaiement(DetailsPaiement):
    model_config = ConfigDict(from_attributes=True)


class InnerDetailsPaiementResponse(BaseModel):
    ligne_financiere_id: int

    dps: list[DetailsPaiement]


class DetailsPaiementResponse(APISuccess[InnerDetailsPaiementResponse]):
    pass


@router.get(
    "/{id_ae:int}/details-paiement",
    summary="Récupére les détails de paiement associés à une ligne financière de type AE",
    response_model=DetailsPaiementResponse,
    responses=error_responses(),
)
def get_details_paiement_pour_ligne_financiere(
    id_ae: int,
    session: Session = Depends(get_session_main),
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
):
    source_query_params = SourcesQueryParams(source=DataType.FINANCIAL_DATA_AE)
    source_query_params = enforce_query_params_with_connected_user_rights(source_query_params, user)

    assert source_query_params.source_region is not None or source_query_params.data_source is not None, (
        "Au moins un des paramètres source_datatype ou data_source doit être fourni"
    )

    ligne = get_ligne(session, source_query_params, id_ae)

    if ligne is None:
        logger.debug(f"Aucun détails de paiement trouvé pour l'ae avec l'id {id_ae}")
        dps = []
    else:
        stmt = select(FinancialCp).where(FinancialCp.id_ae == ligne.id)
        execution = session.execute(stmt)
        results = execution.scalars().all()
        dps = [InnerDetailsPaiement.model_validate(dp) for dp in results]

    data = InnerDetailsPaiementResponse(
        ligne_financiere_id=id_ae,
        dps=dps,
    )
    response_model = DetailsPaiementResponse(
        code=200,
        message=f"Détails de paiement pour la ligne financière {id_ae}",
        data=data,
    )
    response = response_model.to_json_response()
    return response
