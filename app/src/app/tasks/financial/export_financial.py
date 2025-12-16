from datetime import datetime, timezone
import os
from celery import current_task

from models.entities.audit.ExportFinancialTask import ExportFinancialTask
from services.audits.export_financial_task import ExportFinancialTaskService
from services.budget.query_builder import BudgetQueryBuilder
from services.budget.query_params import BudgetQueryParams

from app import celeryapp, db
from app.tasks.financial import logger


celery = celeryapp.celery


@celery.task(bind=True, name="export_run_financial")
def export_run_financial(self, task_id: int):
    try:
        # Set de la task en RUNNING
        task: ExportFinancialTask = ExportFinancialTaskService.find_by_id(task_id)
        task.status = "RUNNING"
        task.celery_task_id = current_task["request"]["id"]
        task.started_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"[EXPORT][LIGNES] Tâche d'export {task.download_code} lancée.")

        # Création du builder pour récupérer les lignes financières
        params: BudgetQueryParams = _rebuild_budget_query_params(task.params)
        builder = (
            BudgetQueryBuilder(db.session, params)
            .beneficiaire_siret_in(params.beneficiaire_code)
            .code_programme_in(params.code_programme)
            .themes_in(params.theme)
            .annee_in(params.annee)
            .niveau_code_geo_in(params.niveau_geo, params.code_geo, params.source_region)
            .annee_in(params.annee)
            .centres_couts_in(params.centres_couts)
            .domaine_fonctionnel_in(params.domaine_fonctionnel)
            .referentiel_programmation_in(params.referentiel_programmation)
            .n_ej_in(params.n_ej)
            .source_is(params.source)
            .data_source_is(params.data_source)
            .source_region_in(params.source_region)
            .categorie_juridique_in(
                params.beneficiaire_categorieJuridique_type,
                includes_none=params.beneficiaire_categorieJuridique_type is not None
                and "autres" in params.beneficiaire_categorieJuridique_type,
            )
            .sort_by_params()
            .tags_fullname_in(params.tags)
        )
        print(builder)

        # Création du dossier d'export
        export_dir = os.path.join("/data/partage", str(task.download_code))
        os.makedirs(export_dir, exist_ok=True)
        logger.info(f"[EXPORT][LIGNES] Dossier d'export : /data/partage/{task.download_code}")

        # Récupération paginées des lignes financières && écriture des chunks

        # Ecriture du fichier agrégé final

        # Export fini
        task.status = "DONE"
        task.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        logger.info(f"[EXPORT][LIGNES] Export : /data/partage/{task.download_code}")

        # Mail de notification à envoyer à l'utilisateur task.username

    except Exception:
        logger.exception(f"[EXPORT][LIGNES] Dossier d'export : /data/partage/{task.download_code}")
        task.status = "FAILED"
        db.session.commit()


def _rebuild_budget_query_params(params: dict) -> BudgetQueryParams:
    return BudgetQueryParams(
        source_region=params.get("source_region"),
        data_source=params.get("data_source"),
        source=params.get("source"),
        n_ej=params.get("n_ej"),
        code_programme=params.get("code_programme"),
        niveau_geo=params.get("niveau_geo"),
        code_geo=params.get("code_geo"),
        ref_qpv=params.get("ref_qpv"),
        code_qpv=params.get("code_qpv"),
        theme=params.get("theme"),
        beneficiaire_code=params.get("beneficiaire_code"),
        beneficiaire_categorieJuridique_type=params.get("beneficiaire_categorieJuridique_type"),
        annee=params.get("annee"),
        centres_couts=params.get("centres_couts"),
        domaine_fonctionnel=params.get("domaine_fonctionnel"),
        referentiel_programmation=params.get("referentiel_programmation"),
        tags=params.get("tags"),
        colonnes=params.get("colonnes"),
        # Pagination mise à 1000 pour faire des chunk assez larges
        page=1,
        page_size=1000,
    )
