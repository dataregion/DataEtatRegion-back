from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional
from batches.database import init_persistence_module, session_scope, session_audit_scope
from batches.share.TabularWriter import ExportTarget, TabularWriter

init_persistence_module()
from services.budget.query_params import BudgetQueryParams  # noqa: E402
from services.budget.colonnes import get_list_colonnes_tableau  # noqa: E402
from models.entities.audit.ExportFinancialTask import ExportFinancialTask  # noqa: E402
from services.audits.export_financial_task import ExportFinancialTaskService  # noqa: E402

from prefect import task, flow, runtime  # noqa: E402
from prefect.cache_policies import NO_CACHE  # noqa: E402

PAGE_SIZE = 1000

from batches.filesystem import get_dossier_exports_path  # noqa: E402


def _entity_to_colonnes(entity, colonnes: list[str]) -> list[str]:
    lst = [getattr(entity, col) for col in colonnes]
    return lst


@dataclass(frozen=True)
class _Ctx:
    ### informations sur la cible de l'export
    target_format: ExportTarget = "csv"
    """Type de fichier d'export (csv, xlsx, etc)"""
    current_export_dir: Optional[Path] = None
    """Répertoire courant d'export"""

    @property
    def current_export_file(self) -> Optional[Path]:
        if self.current_export_dir is None:
            return None
        return self.current_export_dir / "export_file"

    ### budget query params
    query_params: Optional[BudgetQueryParams] = None
    """Paramètres de la requête d'export"""

    # Metadonnées sur l'état de l'export
    nb_lignes: int = 0
    """Nombre de lignes exportées"""
    current_page: int = 1
    """Page courante"""
    page_size: int = PAGE_SIZE
    """Taille de page"""
    has_next: bool = True
    """Indique s'il y a une page suivante"""

    ##
    id_of_export_entity: Optional[int] = None


@task(timeout_seconds=60, log_prints=True, cache_policy=NO_CACHE)
def initialise_export_task_in_db(ctx: _Ctx) -> _Ctx:
    user_email: str = runtime.flow_run.parameters["user_email"]  # type: ignore
    export_pretty_name: str = runtime.flow_run.parameters["pretty_name"]  # type: ignore
    flow_run_id = runtime.flow_run.id  # type: ignore
    assert user_email is not None
    assert flow_run_id is not None

    with session_audit_scope() as session:
        export_entity: ExportFinancialTask = ExportFinancialTaskService.initialize_and_persist_export_task_entity(
            session,
            user_email,
            prefect_id=flow_run_id,
            name=export_pretty_name,
        )
        export_entity.target_format = ctx.target_format  # type: ignore
        session.commit()
        ctx = replace(ctx, id_of_export_entity=export_entity.id)
    return ctx


@task(timeout_seconds=60, log_prints=True, cache_policy=NO_CACHE)
def initialise_query_params(ctx: _Ctx) -> _Ctx:
    params: BudgetQueryParams = runtime.flow_run.parameters["filters"]  # type: ignore
    ctx = replace(ctx, query_params=params)
    return ctx


@task(timeout_seconds=60, log_prints=True, cache_policy=NO_CACHE)
def initalise_fs(ctx: _Ctx) -> _Ctx:
    flow_name = runtime.flow_run.flow_name  # type: ignore
    flow_run_id = runtime.flow_run.id  # type: ignore

    current_partage_path = get_dossier_exports_path() / f"{flow_name}" / f"{flow_run_id}"
    current_partage_path.mkdir(parents=True, exist_ok=True)

    ctx = replace(ctx, current_export_dir=current_partage_path)

    ### Vide le fichier d'export s'il existe déjà
    assert ctx.current_export_file is not None
    with ctx.current_export_file.open("wb"):
        pass

    ###
    assert ctx.query_params is not None
    params: BudgetQueryParams = ctx.query_params
    writer = TabularWriter.create_writer(
        filep=str(ctx.current_export_file),
        export_target=ctx.target_format,
    )
    colonnes = params.colonnes_list
    if colonnes is None:
        colonnes = list(map(lambda c: str(c.code), get_list_colonnes_tableau()))

    params = params.with_update({"colonnes": ",".join(colonnes)})
    ctx = replace(ctx, query_params=params)
    writer.write_header(colonnes)
    writer.close()
    ####

    return ctx


@task(timeout_seconds=60, log_prints=True, cache_policy=NO_CACHE)
def step(ctx: _Ctx) -> _Ctx:
    print(f"Requête la page {ctx.current_page}, size: {ctx.page_size}")

    assert ctx.query_params is not None
    params: BudgetQueryParams = ctx.query_params
    params = params.with_update({"page": ctx.current_page, "page_size": ctx.page_size})
    assert params.source_region is not None

    from services.budget.lignes_financieres.get_data import get_lignes

    with session_scope() as session:
        data, has_next, grouped, builder = get_lignes(db=session, params=params)
        assert grouped is False, "Un export ne devrait pas pouvoir se faire sur un grouping!"

        ###
        assert ctx.current_export_dir is not None, (
            "Le répertoire d'export doit être initialisé avant d'écrire des données"
        )
        writer = TabularWriter.create_writer(
            filep=str(ctx.current_export_file),
            export_target=ctx.target_format,
        )
        values = list(map(lambda e: _entity_to_colonnes(e, params.colonnes_list), data))  # type: ignore
        writer.write_rows(values)
        writer.close()

        ctx = replace(
            ctx,
            has_next=has_next,
            nb_lignes=ctx.nb_lignes + len(data),
        )
        ###
        return ctx


@flow(log_prints=True)
def exporte_une_recherche(
    user_email: str,
    pretty_name: str,
    format: ExportTarget,
    filters: BudgetQueryParams,
):
    ctx = _Ctx(target_format=format)
    ctx = initialise_export_task_in_db(ctx)
    ctx = initialise_query_params(ctx)
    ctx = initalise_fs(ctx)
    ctx = step(ctx)
    while ctx.has_next:
        ctx = replace(ctx, current_page=ctx.current_page + 1)
        ctx = step(ctx)

    print(f"Export terminé, {ctx.nb_lignes} lignes exportées.")

    with session_audit_scope() as session:
        filep = str(ctx.current_export_file)
        task_id = ctx.id_of_export_entity
        assert task_id is not None
        ExportFinancialTaskService.complete_export_task_entity(session, task_id, filep)


if __name__ == "__main__":  # Pour le debug
    exporte_une_recherche("csm@sib.fr", "Export de test", "csv", BudgetQueryParams.make_default())
