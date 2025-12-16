from sqlalchemy.orm import Session


from prefect.deployments import run_deployment
from services.audits.export_financial_task import ExportFinancialTaskService
from services.budget.query_params import BudgetQueryParams
from models.value_objects.export_api import ExportTarget


import datetime


def do_export(
    session: Session,
    user_email: str,
    format: ExportTarget,
    params: BudgetQueryParams,
):
    """Lance un export de lignes budgetaires"""
    # Sauvegarde de la tâche d'export
    raw_params = vars(params)
    stripped_params = {k: v for k, v in raw_params.items() if k not in {"page", "page_size", "search", "fields_search"}}

    pretty_name = f"Export de votre recherche du {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    run = run_deployment(
        name="exporte-une-recherche/exporte_une_recherche",
        parameters={
            "filters": stripped_params,
            "user_email": user_email,
            "pretty_name": pretty_name,
            "format": format,
        },
        timeout=0,  # fire and forget
    )

    run_id = str(run.id)
    task = ExportFinancialTaskService.initialize_and_persist_export_task_entity(
        session,
        user_email,
        run_id,
        pretty_name,
        format,
    )

    return task
