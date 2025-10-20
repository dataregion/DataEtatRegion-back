import logging
from apis.config.current import get_config
from services.utilities.observability import cache_stats

from apis.apps.budget.models.budget_query_params import FinancialLineQueryParams
from apis.apps.budget.services.query_builder import FinancialLineQueryBuilder

from cachetools import cached, LRUCache
from cachetools.keys import hashkey

from apis.services.pubsub import on_channel
from models.value_objects.redis_events import MAT_VIEWS_REFRESHED_EVENT_CHANNEL

logger = logging.getLogger(__name__)

_size = get_config().cache_config.budget_totaux_size
total_cache = LRUCache(maxsize=_size)


@on_channel(MAT_VIEWS_REFRESHED_EVENT_CHANNEL)
async def clear_cache_total_of_lignes(message):
    logger.info(
        "Réception d'un événement de rafraîchissement des vues matérialisées, vidage du cache des totaux des lignes financières."
    )
    total_cache.clear()


def _cache_key(
    params: FinancialLineQueryParams, additionnal_source_region: str | None, builder: FinancialLineQueryBuilder
):
    """
    Calcule une clé de cache unique pour les paramètres donnés.
    Renvoie None si les paramètres ne sont pas cacheables.
    """
    params_cache_key = params.get_total_cache_key()
    key = (
        (
            "GetTotalOfLignes",
            params_cache_key,
            additionnal_source_region,
        )
        if params_cache_key is not None
        else None
    )

    return hashkey(key)


@cache_stats()
@cached(total_cache, key=_cache_key, info=True)
def _cached_retrieve(
    params: FinancialLineQueryParams, additionnal_source_region: str | None, builder: FinancialLineQueryBuilder
):
    return _retrieve(params, additionnal_source_region, builder)


def _retrieve(
    params: FinancialLineQueryParams, additionnal_source_region: str | None, builder: FinancialLineQueryBuilder
):
    return builder.get_total("groupings" if builder.groupby_colonne else "lignes")


class GetTotalOfLignes:
    """Service applicatif pour la récupération du total des lignes financières."""

    def __init__(self, builder: FinancialLineQueryBuilder) -> None:
        self._builder = builder
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def retrieve_total(
        self,
        params: FinancialLineQueryParams,
        additionnal_source_region: str | None = None,
    ):
        is_cache_enable = get_config().cache_config.budget_totaux_enabled
        key = params.get_total_cache_key()

        do_use_cache = is_cache_enable and key is not None

        if not do_use_cache:
            result = _retrieve(params, additionnal_source_region, self._builder)
        else:
            self._logger.info("Utilise le cache pour la récupération des totaux")
            result = _cached_retrieve(params, additionnal_source_region, self._builder)

        return result
