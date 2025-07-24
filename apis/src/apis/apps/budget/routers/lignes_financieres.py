from http import HTTPStatus
import logging

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from models.value_objects.common import DataType

from apis.apps.budget.models.grouped_data import GroupedData
from apis.apps.budget.models.budget_query_params import FinancialLineQueryParams, SourcesQueryParams
from apis.apps.budget.services.get_colonnes import get_list_colonnes_grouping
from apis.apps.budget.services.get_data import get_annees_budget, get_ligne, get_lignes
from apis.database import get_db
from apis.security import ConnectedUser, get_connected_user
from apis.shared.decorators import handle_exceptions
from apis.shared.models import APIError, APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)

def handle_national(params: FinancialLineQueryParams, user: ConnectedUser) -> FinancialLineQueryParams:
    if user.current_region != "NAT":
        params.source_region = user.current_region
    else:
        params.data_source = "NATION"
    return params

@router.get("", summary="Récupére les lignes financières, mécanisme de grouping pour récupérer les montants agrégés", response_class=JSONResponse)
@handle_exceptions
def get_lignes_financieres(params: FinancialLineQueryParams = Depends(), db: Session = Depends(get_db)):
    user = ConnectedUser({"region": "053"})
    print(user.current_region)
    params = handle_national(params, user)
    if params.grouping is not None:
        params.map_colonnes(get_list_colonnes_grouping())
    
    message = "Liste des données financières"
    data, grouped, has_next = get_lignes(db, params)
    if grouped:
        message = "Liste des montants agrégés"
        data = [GroupedData(**d).to_dict() for d in data]
    else:
        data = EnrichedFlattenFinancialLinesSchema(many=True).dump(data)

    if len(data) == 0:
        return APISuccess(
            code=HTTPStatus.NO_CONTENT,
            message="Aucun résultat ne correspond à vos critères de recherche",
            data=[],
        ).to_json_response()
    
    return APISuccess(
        code=HTTPStatus.OK,
        message=message,
        data=data,
        has_next=has_next,
        current_page=params.page
    ).to_json_response()


@router.get("/{id:int}", summary="Récupére les infos budgetaires en fonction de son identifiant technique", response_class=JSONResponse)
@handle_exceptions
def get_lignes_financieres_by_source(id: int, params: SourcesQueryParams = Depends(), db: Session = Depends(get_db), user: ConnectedUser = Depends(get_connected_user)):
    
    if not params.source:
        return APIError(
            code=HTTPStatus.UNPROCESSABLE_ENTITY,
            error="La paramètre `source` est requis."
        ).to_json_response()
    
    params = handle_national(params, user)

    ligne = get_ligne(db, params, id)
    if ligne is None:
        return APISuccess(
            code=HTTPStatus.NO_CONTENT,
            message="Aucun résultat ne correspond à vos critères de recherche",
            data=[],
        ).to_json_response()
    
    return APISuccess(
        code=HTTPStatus.OK,
        message="Ligne financière",
        data=EnrichedFlattenFinancialLinesSchema().dump(ligne)
    ).to_json_response()


@router.get("/annees", summary="Recupère la plage des années pour lesquelles les données budgetaires courent.", response_class=JSONResponse)
@handle_exceptions
def get_annees(params: SourcesQueryParams = Depends(), db: Session = Depends(get_db), user: ConnectedUser = Depends(get_connected_user)):
    params = handle_national(params, user)
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des années présentes dans les lignes financières",
        data=get_annees_budget(db, params)
    ).to_json_response()




