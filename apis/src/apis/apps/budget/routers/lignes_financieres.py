from http import HTTPStatus
import logging
import os
from types import NoneType
from typing import Mapping, TypeVar

from fastapi import APIRouter, Depends
from fastapi.responses import FileResponse
from models.entities.audit.ExportFinancialTask import ExportFinancialTask
from services.audits.export_financial_task import ExportFinancialTaskService
from sqlalchemy.orm import Session

from models.connected_user import ConnectedUser
from models.schemas.financial import EnrichedFlattenFinancialLinesSchema
from models.value_objects.grouped_data import GroupedData
from models.value_objects.export_api import ExportTarget, is_file_format
from services.budget.query_params import BudgetQueryParams
from services.shared.source_query_params import SourcesQueryParams

from apis.apps.budget.routers.api_models import ExportFinancialTask as ExportFinancialTaskDTO
from apis.apps.budget.routers.api_models import Groupings, LigneFinanciere, LignesFinancieres
from apis.apps.budget.services.exports import do_export as service_do_export
from apis.apps.budget.services.get_data import get_annees_budget, get_ligne, get_lignes
from apis.database import get_session_main, get_session_audit
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
        params = params.with_update(update={"source_region": user.current_region})
    else:
        params = params.with_update(update={"data_source": "NATION"})
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
    session: Session = Depends(get_session_main),
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
    session: Session = Depends(get_session_main),
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
    session: Session = Depends(get_session_main),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    params = handle_national(params, user)
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des années présentes dans les lignes financières",
        data=get_annees_budget(session, params),
    ).to_json_response()


class DoExportResponse(APISuccess[ExportFinancialTaskDTO]):
    pass


@router.post(
    "/export",
    summary="Enregistre une tâche d'export des lignes financières",
    response_model=DoExportResponse,
    responses=error_responses(),
)
def do_export(
    session_audit: Session = Depends(get_session_audit),
    params: BudgetQueryParams = Depends(),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
    format: ExportTarget = "csv",
):
    params = handle_national(params, user)
    task = service_do_export(session_audit, user.email, format, params)
    dto = ExportFinancialTaskDTO.model_validate(task)
    return APISuccess(code=HTTPStatus.OK, message="Export fraichement lancé.", data=dto)


class ExportsResponse(APISuccess[list[ExportFinancialTaskDTO]]):
    pass


@router.get(
    "/exports",
    summary="Liste les tâches d'export des lignes financières",
    response_model=ExportsResponse,
    responses=error_responses(),
)
def list_exports(
    session_audit: Session = Depends(get_session_audit),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    tasks = ExportFinancialTaskService.find_all_file_exports_by_username(session_audit, user.email)
    dtos = [ExportFinancialTaskDTO.model_validate(x) for x in tasks]
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des tâches d'export",
        data=dtos,
    ).to_json_response()


ExportResponse = DoExportResponse


@router.get(
    "/export/{uuid:str}",
    summary="Récupère les informations d'un export",
    response_model=ExportResponse,
    responses=error_responses(),
)
def get_export(
    uuid: str,
    session_audit: Session = Depends(get_session_audit),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    run_id = uuid
    task = ExportFinancialTaskService.find_by_run_id(session_audit, run_id)
    dto = ExportFinancialTaskDTO.model_validate(task)
    if task.username != user.email:
        return APIError(
            code=HTTPStatus.FORBIDDEN.value, message="Vous n'êtes pas autorisé à consulter cet export."
        ).to_json_response()
    return APISuccess(
        code=HTTPStatus.OK,
        message=f"Export {run_id}",
        data=dto,
    ).to_json_response()


@router.get(
    "/download/{uuid:str}",
    summary="Télécharge un export existant selon son id",
    responses=error_responses(),
)
def download_export(
    uuid: str,
    session_audit: Session = Depends(get_session_audit),
    user: ConnectedUser = Depends(keycloak_validator.get_connected_user()),
):
    run_id = uuid
    task: ExportFinancialTask = ExportFinancialTaskService.find_by_run_id(session_audit, run_id)

    # Validation basique
    if not task:
        return APIError(code=HTTPStatus.NOT_FOUND.value, message="Aucun export associé à ce code.").to_json_response()
    if task.username != user.email:
        return APIError(
            code=HTTPStatus.FORBIDDEN.value, message="Vous n'êtes pas autorisé à télécharger cet export."
        ).to_json_response()
    if task.status != "DONE":
        return APIError(
            code=HTTPStatus.BAD_REQUEST.value, message="Export non disponible disponible au téléchargement."
        ).to_json_response()
    if task.target_format is None or is_file_format(task.target_format) is False:
        return APIError(
            code=HTTPStatus.BAD_REQUEST.value, message="Export non disponible disponible au téléchargement."
        ).to_json_response()

    # Le fichier existe ?
    if not os.path.exists(task.file_path):
        logger.error(f"Le fichier '{task.file_path}' n'existe pas.")
        return APIError(
            code=HTTPStatus.NOT_FOUND.value, message=f"Le fichier '{format}' n'est pas disponible pour cet export."
        ).to_json_response()

    # Retour du fichier
    media_types: Mapping[ExportTarget, str] = {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        "ods": "application/vnd.oasis.opendocument.spreadsheet",
    }
    media_type = media_types[task.target_format]
    return FileResponse(
        path=task.file_path,
        media_type=media_type,
        filename=f"export.{str(task.target_format)}",
    )
