from http import HTTPStatus
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from services.utilities.observability import SummaryOfTimePerfCounter

from apis.apps.budget.models.budget_query_params import FinancialLineQueryParams
from apis.apps.budget.services.get_data import get_lignes
from apis.database import get_session
from apis.shared.decorators import handle_exceptions
from apis.shared.models import APISuccess
from apis.shared.openapi_config import build_api_success_response


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "",
    summary="Vérification de la disponibilité de l'API des lignes budgetaires",
    response_class=JSONResponse,
    responses=build_api_success_response(),
)
@handle_exceptions
def healthcheck(
    session: Session = Depends(get_session),
    params: FinancialLineQueryParams = Depends(),
):
    params.colonnes = [ "source" ]
    params.source_region = "053"
    params.page = 1
    params.page_size = 10

    with SummaryOfTimePerfCounter.cm("hc_search_lignes_budgetaires"):
        data, grouped, has_next = get_lignes(session, params)

    with SummaryOfTimePerfCounter.cm("hc_serialize_lignes_budgetaires"):
        data = EnrichedFlattenFinancialLinesSchema(many=True).dump(data)

    assert len(data) == 10

    return APISuccess(
        code=HTTPStatus.OK,
        message="API is running !",
        data=None,
    )
