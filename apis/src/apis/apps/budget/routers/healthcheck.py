from http import HTTPStatus
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from services.utilities.observability import SummaryOfTimePerfCounter

from apis.apps.budget.models.budget_query_params import FinancialLineQueryParams
from apis.apps.budget.services.get_data import get_lignes
from apis.database import get_db
from apis.security import ConnectedUser, get_connected_user
from apis.shared.decorators import handle_exceptions
from apis.shared.models import APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("", summary="Vérification de la disponibilité de l'API des lignes budgetaires")
@handle_exceptions
def healthcheck(db: Session = Depends(get_db), params: FinancialLineQueryParams = Depends()):
    params.colonnes = "source"
    params.source_region = "053"
    params.page = 1
    params.page_size = 10

    with SummaryOfTimePerfCounter.cm("hc_search_lignes_budgetaires"):
        data, grouped, has_next = get_lignes(db, params)

    with SummaryOfTimePerfCounter.cm("hc_serialize_lignes_budgetaires"):
        data = EnrichedFlattenFinancialLinesSchema(many=True).dump(data)

    assert len(data) == 10

    return APISuccess(
        code=HTTPStatus.OK,
        message="API /v3/budget is running !",
        data=None,
    ).to_json_response()
