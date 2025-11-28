from http import HTTPStatus
import logging
import requests
from types import NoneType
from typing import TypeVar

from fastapi import APIRouter, Depends
from models.entities.audit.ExportFinancialTask import ExportFinancialTask
from services.audits.export_financial_task import ExportFinancialTaskService
from sqlalchemy.orm import Session

from models.connected_user import ConnectedUser
from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from models.value_objects.grouped_data import GroupedData
from services.budget.query_params import BudgetQueryParams
from services.shared.source_query_params import SourcesQueryParams

from apis.apps.budget.routers.api_models import Groupings, LigneFinanciere, LignesFinancieres
from apis.apps.budget.services.get_data import get_annees_budget, get_ligne, get_lignes
from apis.database import get_session
from apis.exception_handlers import error_responses
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.services.model.pydantic_annotation import make_pydantic_annotation_from_marshmallow_lignes
from apis.shared.models import APIError, APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()

PydanticEnrichedFlattenFinancialLinesModel = make_pydantic_annotation_from_marshmallow_lignes(
    EnrichedFlattenFinancialLinesSchema, True
)

_params_T = TypeVar("_params_T", bound=SourcesQueryParams)


def handle_national(params: _params_T, user: ConnectedUser) -> _params_T:
    """Replace les paramètres en premier argument avec la source_region / data_source de la connexion utilisateur"""
    if user.current_region != "NAT":
        params.source_region = user.current_region
    else:
        params.data_source = "NATION"
    return params


class LignesResponse(APISuccess[LignesFinancieres | Groupings | NoneType]):
    pass


class LigneResponse(APISuccess[LigneFinanciere]):
    pass


@router.get(
    "",
    summary="Récupére les lignes financières, mécanisme de grouping pour récupérer les montants agrégés",
    response_model=LignesResponse,
    responses=error_responses(),
)
def get_lignes_financieres(
    params: BudgetQueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
    force_no_cache: bool = False,
):
    user_param_source_region = params.source_region
    params = handle_national(params, user)

    message = "Liste des données financières"
    data, total, grouped, has_next = get_lignes(
        session,
        params,
        additionnal_source_region=user_param_source_region,
        force_no_cache=force_no_cache,
    )
    size = len(data)
    if grouped:
        message = "Liste des montants agrégés"
        data = [GroupedData(**d) for d in data]
        for d in data:
            d.colonne = params.grouping_list[-1].code
        data = Groupings(total=total, groupings=data)
    else:
        data = LignesFinancieres(total=total, lignes=data)

    if size == 0:
        return APISuccess(
            code=HTTPStatus.NO_CONTENT,
            message="Aucun résultat ne correspond à vos critères de recherche",
            data=None,
        ).to_json_response()

    return LignesResponse(
        code=HTTPStatus.OK,
        message=message,
        data=data,
        has_next=has_next,
        current_page=params.page,
    )


@router.get(
    "/{id:int}",
    summary="Récupére les infos budgetaires en fonction de son identifiant technique",
    response_model=LigneResponse,
    responses=error_responses(),
)
def get_lignes_financieres_by_source(
    id: int,
    params: SourcesQueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    if not params.source:
        return APIError(
            code=HTTPStatus.UNPROCESSABLE_ENTITY,
            detail="La paramètre `source` est requis.",
        ).to_json_response()

    params = handle_national(params, user)

    ligne = get_ligne(session, params, id)
    if ligne is None:
        return APIError(
            code=HTTPStatus.NOT_FOUND,
            message="Aucun résultat ne correspond à vos critères de recherche",
        ).to_json_response()

    return LigneResponse(
        code=HTTPStatus.OK,
        message="Ligne financière",
        data=ligne,
    ).to_json_response()


@router.get(
    "/annees",
    summary="Recupère la plage des années pour lesquelles les données budgetaires courent.",
    response_model=APISuccess[list[int]],
    responses=error_responses(),
)
def get_annees(
    params: SourcesQueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    params = handle_national(params, user)
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des années présentes dans les lignes financières",
        data=get_annees_budget(session, params),
    )


def _get_user() -> ConnectedUser:
    return ConnectedUser(
        {
            "email": "benjamin.bagot@sib.fr",
            "username": "benjamin.bagot@sib.fr",
            "region": "053",
        }
    )


@router.post(
    "/export",
    summary="Enregistre une tâche d'export des lignes financières",
    responses=error_responses(),
)
def prepare_export(
    params: BudgetQueryParams = Depends(),
    session: Session = Depends(get_session),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    # Validation et mise en forme des paramètres
    user_param_source_region = params.source_region
    params = handle_national(params, user)
    params.source_region = (
        user_param_source_region if not params.source_region else params.source_region + "," + user_param_source_region,
    )

    # Sauvegarde de la tâche d'export
    raw_params = vars(params)
    stripped_params = {k: v for k, v in raw_params.items() if k not in {"page", "page_size", "search", "fields_search"}}
    task: ExportFinancialTask = ExportFinancialTaskService.save_new_export(session, user.email, stripped_params)

    # Appel API à app pour lancer la tâche d'export
    try:
        url: str = "http://data-transform-api/financial-data/api/v2/budget/export"
        requests.post(url, json={"task_id": task.id})
        return APISuccess(
            code=HTTPStatus.OK,
            message="Export en cours, vous recevrez un lien de téléchargement par mail une fois terminé.",
            data=None,
        )

    except Exception as e:
        task.status = "FAILED"
        session.commit()
        return APIError(
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR, detail=f"Impossible de déclencher la tâche : {str(e)}"
        )


# @router.post(
#     "/download/{uuid}",
#     summary="Enregistre une tâche d'export des lignes financières",
#     responses=error_responses(),
# )
# def download_export(
#     # uuid: str = Depends(),
#     # format: str = Query("csv", regex="^(csv|xlsx|ods)$"),
#     session: Session = Depends(get_session),
#     user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
# ):
#     task: ExportFinancialTask = ExportFinancialTaskService.find_by_uuid(session, "uuid")

#     if not task:
#         raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail="Aucun export associé à ce code.")
#     if task.username != user.email:
#         raise HTTPException(status_code=HTTPStatus.FORBIDDEN, detail="Vous n'êtes pas autorisé à télécharger cet export.")
#     if task.status != "DONE":
#         raise HTTPException(status_code=HTTPStatus.BAD_REQUEST, detail=f"Export non disponible.")

#     base_path = task.file_path
#     root, _ = os.path.splitext(base_path)
#     requested_file = f"{root}.{format}"
#     if not os.path.exists(requested_file):
#         raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail=f"Le fichier '{format}' n'est pas disponible pour cet export.")

#     media_types = {
#         "csv": "text/csv",
#         "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
#         "ods": "application/vnd.oasis.opendocument.spreadsheet"
#     }
#     return FileResponse(
#         path=requested_file,
#         media_type=media_types[format],
#         filename=f"export.{format}",
#     )
