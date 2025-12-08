from http import HTTPStatus
import logging

from fastapi import APIRouter, Depends
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from services.utilities.observability import SummaryOfTimePerfCounter

from services.qpv.query_params import QpvQueryParams
from apis.apps.qpv.services.get_data import get_lignes
from apis.database import get_session
from apis.exception_handlers import error_responses
from apis.shared.models import APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)


@router.get(
    "",
    summary="Vérification de la disponibilité de l'API des lignes QPV",
    response_class=JSONResponse,
    responses=error_responses(),
)
def healthcheck(
    session: Session = Depends(get_session),
    params: QpvQueryParams = Depends(),
):
    params = params.with_update(
        update={
            "colonnes": "source",
            "source_region": "053",
            "page": 1,
            "page_size": 10,
        }
    )

    with SummaryOfTimePerfCounter.cm("hc_search_lignes_qpv"):
        data, has_next = get_lignes(session, params)

    with SummaryOfTimePerfCounter.cm("hc_search_lignes_qpv"):
        data = EnrichedFlattenFinancialLinesSchema(many=True).dump(data)

    assert len(data) == 10

    return APISuccess(
        code=HTTPStatus.OK,
        message="API is running !",
        data=None,
    )
