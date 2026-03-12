from datetime import datetime
from dataclasses import dataclass, field

from api_entreprise import ApiEntreprise, ApiError
from api_entreprise.exceptions import LimitHitError
from prefect import flow, task, get_run_logger
from prefect.concurrency.sync import concurrency
from prefect.cache_policies import NO_CACHE
from sqlalchemy import select, func, asc

from batches.config.current import get_config
from batches.database import init_persistence_module, session_scope
from batches.prefect.utils import ensure_concurrency_limit

init_persistence_module()

from services.refs.siret import ApiGeoClient, UpdateRefSiretService  # noqa: E402

from models.entities.refs.Siret import Siret  # noqa: E402
from models.value_objects.api_entreprise_info import ApiEntrepriseInfo  # noqa: E402

# ──────────────────────────────────────────────
# Constantes
# ──────────────────────────────────────────────
UPDATE_SIRET_CONCURRENCY_ID = "update_all_siret"
"""Nombre maximum de SIRETs à traiter par exécution du flow."""


def _get_logger():
    """Wrapper pour get_run_logger, patchable dans les tests."""
    return get_run_logger()


def _info(text: str, logger):
    logger.info(f"[TASK][UPDATE_SIRET] {text}")


# ──────────────────────────────────────────────
# Contexte du flow
# ──────────────────────────────────────────────
@dataclass
class UpdateSiretFlowContext:
    max_sirets: int
    """Nombre maximum de SIRETs à traiter."""

    processed: int = 0
    """Nombre de SIRETs traités."""

    success: int = 0
    """Nombre de SIRETs traités avec succès."""

    errors: int = 0
    """Nombre de SIRETs en erreur."""

    total_in_db: int = 0
    """Nombre total de SIRETs en BDD."""

    sirets_in_error: list[str] = field(default_factory=list)
    """Liste des codes SIRET en erreur."""


@dataclass
class UpdateOneSiretResult:
    success: bool
    siret: str


# ──────────────────────────────────────────────
# Factory du client API entreprise
# ──────────────────────────────────────────────
def _make_api_entreprise_client(api_config: ApiEntrepriseInfo) -> ApiEntreprise:
    """Construit le client API entreprise à partir de la configuration batches."""
    from services.apis_externes.clients.entreprise.factory import make_api_entreprise
    from models.value_objects.api_entreprise_info import ApiEntrepriseInfo

    api_info = ApiEntrepriseInfo(
        url=api_config.url,
        token=api_config.token,
        context=api_config.context,
        recipient=api_config.recipient,
        object=api_config.object,
        timeout_seconds=api_config.timeout_seconds,
    )

    client = make_api_entreprise(api_info)
    if client is None:
        raise RuntimeError("Impossible de créer le client API entreprise")
    return client


# ──────────────────────────────────────────────
# Factory du service d'update siret
# ──────────────────────────────────────────────
def _make_update_ref_siret_service(api_entreprise: ApiEntreprise):
    api_geo_url = get_config().api_geo_url
    service = UpdateRefSiretService(api_entreprise, ApiGeoClient(api_geo_url))
    return service


# ──────────────────────────────────────────────
# Tâche Prefect : mise à jour d'un seul SIRET
# ──────────────────────────────────────────────


@task(timeout_seconds=120, log_prints=True, cache_policy=NO_CACHE, retries=0)
async def update_one_siret(siret: str) -> UpdateOneSiretResult:
    """Met à jour un SIRET via l'API entreprise.

    Returns:
        None si succès, le code SIRET en cas d'erreur.
    """
    config = get_config()
    api_entreprise = _make_api_entreprise_client(config.api_entreprise)
    return await _update_one_siret(siret, api_entreprise)


async def _update_one_siret(siret: str, api_entreprise: ApiEntreprise):
    logger = _get_logger()

    update_siret_service = _make_update_ref_siret_service(api_entreprise)

    # Repère l'établissement
    try:
        etablissement = api_entreprise.donnees_etablissement(siret)
    except LimitHitError as e:
        logger.error(f"[UPDATE_SIRET] {siret} : Limite API atteinte.", exc_info=e)
        return UpdateOneSiretResult(success=False, siret=str(siret))
    except ApiError as e:
        logger.error(f"[UPDATE_SIRET] Erreur API entreprise pour le SIRET {siret}", exc_info=e)
        return UpdateOneSiretResult(success=False, siret=str(siret))

    # Met à jour le ret_siret
    success = True
    with session_scope() as session:
        if etablissement is None:
            logger.warning(f"SIRET {siret} : Aucune donnée retournée par l'API.")
            success = False

        siret_entity = update_siret_service.update_siret_from_api_entreprise_payload(
            session, str(siret), etablissement, insert_only=False
        )
        _ = update_siret_service.fill_commune_info(session, siret_entity)

        # Force la mise à jour de l'updated_at
        siret_entity.updated_at = datetime.now()

        session.add(siret_entity)

    _info(f"SIRET {siret} : mis à jour avec succès", logger)
    return UpdateOneSiretResult(success=success, siret=str(siret))


# ──────────────────────────────────────────────
# Flow Prefect
# ──────────────────────────────────────────────
@flow(log_prints=True, timeout_seconds=3 * 60 * 60)
async def update_all_sirets(max_sirets: int | None = None):
    """Flow de mise à jour des SIRETs via l'API entreprise.

    Le flow s'arrête après avoir traité `max_sirets` SIRETs (condition d'arrêt).

    Args:
        max_sirets: Nombre maximum de SIRETs à traiter.
    """
    logger = _get_logger()
    await ensure_concurrency_limit(UPDATE_SIRET_CONCURRENCY_ID, limit=1, logger=_get_logger())

    with concurrency(UPDATE_SIRET_CONCURRENCY_ID, occupy=1, strict=True):
        config = get_config()
        if config.api_entreprise is None:
            raise RuntimeError(
                "La configuration `api_entreprise` est absente. Veuillez la renseigner dans le fichier de configuration."
            )
        if config.api_geo_url is None:
            raise RuntimeError(
                "La configuration `api_geo_url` est absente. Veuillez la renseigner dans le fichier de configuration."
            )

        max_sirets = max_sirets or config.tasks_config.update_all_sirets.nb_siret_per_run

        _info(f"Démarrage du flow. max_sirets={max_sirets}", logger)
        ctx = UpdateSiretFlowContext(max_sirets=max_sirets)

        # Récupérer tous les codes SIRET (max)
        with session_scope() as session:
            ctx.total_in_db = session.execute(select(func.count(Siret.id))).scalar_one()

            stmt = (
                select(Siret.code)
                .where(Siret.updated_at.is_(None))
                .union_all(select(Siret.code).where(Siret.updated_at.isnot(None)).order_by(asc(Siret.updated_at)))
                .limit(max_sirets)
            )

            sirets = list(session.execute(stmt).scalars())

        assert len(sirets) <= max_sirets

        _info(f"{ctx.total_in_db} SIRETs en base de données", logger)
        _info(f"Traitement de : {ctx.max_sirets} SIRETs", logger)

        # Construire le client API entreprise

        # Traiter les SIRETs
        for siret in sirets:
            # ── Condition d'arrêt ──
            if ctx.processed >= ctx.max_sirets:
                break

            result = await update_one_siret(siret)

            ctx.processed += 1
            if not result.success:
                ctx.errors += 1
                ctx.sirets_in_error.append(result.siret)
            else:
                ctx.success += 1

        # Résumé
        _info(f"Terminé. Traités : {ctx.processed}/{max_sirets} | Erreurs : {ctx.errors}", logger)

        if ctx.sirets_in_error:
            _info(
                f"SIRETs en erreur : {ctx.sirets_in_error[:20]}{'...' if len(ctx.sirets_in_error) > 20 else ''}", logger
            )

        return ctx
