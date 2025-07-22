from http import HTTPStatus

from fastapi import APIRouter

from apis.utils.annotations import handle_exceptions
from apis.utils.models import APISuccess


router = APIRouter()

@router.get("/healthcheck")
@handle_exceptions
def healthcheck():
    # with SummaryOfTimePerfCounter.cm("hc_search_lignes_budgetaires"):
    #     result_q = get_list_colonnes_tableau(
    #         limit=10, page_number=0, source_region="053"
    #     )

    # with SummaryOfTimePerfCounter.cm("hc_serialize_lignes_budgetaires"):
    #     result = EnrichedFlattenFinancialLinesSchema(many=True).dump(result_q["items"])

    # assert len(result) == 10, "On devrait récupérer 10 lignes budgetaires"

    return APISuccess(
        code=HTTPStatus.OK,
        message="API /v3/budget is running !",
        data=None,
    ).to_json_response()
