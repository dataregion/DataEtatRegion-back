from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional
from batches.database import init_persistence_module, session_scope, session_audit_scope
from models.value_objects.export_api import ExportTarget
from batches.share.schemas.ExportEnrichedFlattenFinancialLinesSchema import ExportEnrichedFlattenFinancialLinesSchema
from batches.share.tabular_writer.factory import TabularWriterFactory
from batches.share.tabular_writer.converter import convert_csv_to_excel, convert_csv_to_ods

init_persistence_module()
from services.budget.query_params import BudgetQueryParams  # noqa: E402
from services.budget.colonnes import get_list_colonnes_tableau  # noqa: E402
from models.entities.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLines  # noqa: E402
from models.entities.audit.ExportFinancialTask import ExportFinancialTask  # noqa: E402
from services.audits.export_financial_task import ExportFinancialTaskService  # noqa: E402

from prefect import task, flow, runtime  # noqa: E402
from prefect.cache_policies import NO_CACHE  # noqa: E402


LIMITE_NB_LIGNES_EXPORT = 100_001
PAGE_SIZE = 1000

from batches.filesystem import get_dossier_exports_path  # noqa: E402


def _entity_to_colonnes(dict, colonnes: list[str]) -> list[str]:
    lst = [dict[col] for col in colonnes]
    return lst


def _serialize(ligne: EnrichedFlattenFinancialLines):
    schema = ExportEnrichedFlattenFinancialLinesSchema().enable_safe_getattr()
    obj = schema.dump(ligne)
    return obj


@dataclass(frozen=True)
class _Ctx:
    ### informations sur la cible de l'export
    target_format: ExportTarget = "csv"
    """Type de fichier d'export (csv, xlsx, etc)"""
    current_export_dir: Optional[Path] = None
    """Répertoire courant d'export"""
    needs_conversion: bool = False
    """Indique si on doit convertir le CSV vers un autre format (True pour xlsx/ods)"""

    @property
    def csv_file(self) -> Optional[Path]:
        """Retourne le chemin du fichier CSV (toujours écrit en premier)"""
        if self.current_export_dir is None:
            return None
        return self.current_export_dir / "export_file.csv"

    @property
    def final_export_file(self) -> Optional[Path]:
        """Retourne le chemin du fichier final avec l'extension appropriée"""
        if self.current_export_dir is None:
            return None
        if self.target_format == "xlsx":
            return self.current_export_dir / "export_file.xlsx"
        elif self.target_format == "ods":
            return self.current_export_dir / "export_file.ods"
        else:
            return self.current_export_dir / "export_file.csv"

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

    # Déterminer si on a besoin d'une conversion après l'export CSV
    needs_conversion = ctx.target_format in ["xlsx", "ods"]
    if needs_conversion:
        print(f"Export {ctx.target_format}: écriture en CSV puis conversion vers {ctx.target_format}")

    with session_audit_scope() as session:
        export_entity: ExportFinancialTask = ExportFinancialTaskService.initialize_and_persist_export_task_entity(
            session,
            user_email,
            prefect_id=flow_run_id,
            name=export_pretty_name,
        )
        export_entity.target_format = ctx.target_format  # type: ignore
        session.commit()
        ctx = replace(ctx, id_of_export_entity=export_entity.id, needs_conversion=needs_conversion)
    return ctx


@task(timeout_seconds=60, log_prints=True, cache_policy=NO_CACHE)
def initialise_query_params(ctx: _Ctx) -> _Ctx:
    params: BudgetQueryParams = runtime.flow_run.parameters["filters"]  # type: ignore

    print("On se débarasse de la colonne id pour l'export")
    colonnes = params.colonnes_list
    if colonnes is None:
        colonnes = list(map(lambda c: str(c.code), get_list_colonnes_tableau()))
    if "id" in colonnes:
        colonnes.remove("id")
    params = params.with_update({"colonnes": ",".join(colonnes)})

    ctx = replace(ctx, query_params=params)
    return ctx


@task(timeout_seconds=60, log_prints=True, cache_policy=NO_CACHE)
def initalise_fs(ctx: _Ctx) -> _Ctx:
    flow_name = runtime.flow_run.flow_name  # type: ignore
    flow_run_id = runtime.flow_run.id  # type: ignore

    current_partage_path = get_dossier_exports_path() / f"{flow_name}" / f"{flow_run_id}"
    current_partage_path.mkdir(parents=True, exist_ok=True)

    ctx = replace(ctx, current_export_dir=current_partage_path)

    ### Vide le fichier CSV s'il existe déjà
    assert ctx.csv_file is not None
    with ctx.csv_file.open("wb"):
        pass

    ###
    assert ctx.query_params is not None
    params: BudgetQueryParams = ctx.query_params
    user_email: str = runtime.flow_run.parameters["user_email"]  # type: ignore

    # On écrit toujours en CSV
    writer = TabularWriterFactory.create_writer(
        filep=str(ctx.csv_file),
        export_target="csv",
        username=user_email,
    )
    colonnes = params.colonnes_list

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

    from services.budget.lignes_financieres.get_data import get_lignes

    with session_scope() as session:
        data, has_next, grouped, builder = get_lignes(db=session, params=params)
        data = [_serialize(ligne) for ligne in data]
        assert grouped is False, "Un export ne devrait pas pouvoir se faire sur un grouping!"

        ###
        assert ctx.current_export_dir is not None, (
            "Le répertoire d'export doit être initialisé avant d'écrire des données"
        )

        user_email: str = runtime.flow_run.parameters["user_email"]  # type: ignore

        # On écrit toujours en CSV
        writer = TabularWriterFactory.create_writer(
            filep=str(ctx.csv_file),
            export_target="csv",
            username=user_email,
        )
        values = list(map(lambda e: _entity_to_colonnes(e, params.colonnes_list), data))  # type: ignore
        writer.write_rows(values)
        writer.close()

        nb_lignes = ctx.nb_lignes + len(data)
        ctx = replace(
            ctx,
            has_next=has_next,
            nb_lignes=nb_lignes,
        )

        if nb_lignes > LIMITE_NB_LIGNES_EXPORT:
            raise RuntimeError(f"On limite les exports à {nb_lignes} lignes. On arrête tout.")
        ###
        return ctx


@task(timeout_seconds=120, log_prints=True, cache_policy=NO_CACHE)
def convert_to_final_format(ctx: _Ctx) -> _Ctx:
    """Convertit le CSV vers le format final (Excel ou ODS) si nécessaire."""
    if not ctx.needs_conversion:
        print("Pas de conversion nécessaire, le fichier CSV est le format final")
        return ctx

    assert ctx.csv_file is not None, "Le CSV doit exister"
    assert ctx.final_export_file is not None, "Le fichier final doit être défini"

    csv_path = ctx.csv_file
    target_path = ctx.final_export_file

    if ctx.target_format == "xlsx":
        print(f"Conversion CSV → Excel: {target_path}")
        convert_csv_to_excel(csv_path, target_path, chunk_size=1000)
    elif ctx.target_format == "ods":
        print(f"Conversion CSV → ODS: {target_path}")
        convert_csv_to_ods(csv_path, target_path, chunk_size=1000)
    else:
        raise ValueError(f"Format non supporté pour la conversion: {ctx.target_format}")

    # Supprimer le CSV temporaire
    print(f"Suppression du CSV source: {csv_path}")
    csv_path.unlink()
    print("✓ Conversion terminée et CSV source supprimé")

    return ctx


@flow(log_prints=True)
def exporte_une_recherche(
    user_email: str,
    pretty_name: str,
    format: ExportTarget,
    filters: BudgetQueryParams,
):
    page_size = PAGE_SIZE if format != "to-grist" else 100
    print(f"Initialise l'export. On parcourt les lignes {page_size} par {page_size}.")

    ctx = _Ctx(target_format=format, page_size=page_size)
    ctx = initialise_export_task_in_db(ctx)
    ctx = initialise_query_params(ctx)
    ctx = initalise_fs(ctx)
    ctx = step(ctx)
    while ctx.has_next:
        ctx = replace(ctx, current_page=ctx.current_page + 1)
        ctx = step(ctx)

    print(f"Export terminé, {ctx.nb_lignes} lignes exportées.")

    # Convertir vers le format final si nécessaire (xlsx/ods)
    ctx = convert_to_final_format(ctx)

    # Utiliser le chemin du fichier final
    assert ctx.final_export_file is not None
    filep = str(ctx.final_export_file)

    with session_audit_scope() as session:
        task_id = ctx.id_of_export_entity
        assert task_id is not None
        ExportFinancialTaskService.complete_export_task_entity(session, task_id, filep)


if __name__ == "__main__":  # Pour le debug
    params = BudgetQueryParams.make_default()
    params = params.with_update({"source_region": "53"})
    exporte_une_recherche("csm@sib.fr", "Export de test", "to-grist", params)
