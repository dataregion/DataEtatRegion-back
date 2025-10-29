import logging
from apis.apps.qpv.models.qpv_query_params import QpvQueryParams
from apis.apps.qpv.services.query_builder import QpvQueryBuilder
from apis.config.current import get_config
from services.utilities.observability import cache_stats

from cachetools import cached, LRUCache
from cachetools.keys import hashkey

logger = logging.getLogger(__name__)

_size = get_config().cache_config.budget_totaux_size
total_cache = LRUCache(maxsize=_size)


def _cache_key(params: QpvQueryParams, additionnal_source_region: str | None, builder: QpvQueryBuilder):
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
def _cached_retrieve(params: QpvQueryParams, additionnal_source_region: str | None, builder: QpvQueryBuilder):
    return _retrieve(params, additionnal_source_region, builder)


def _retrieve(params: QpvQueryParams, additionnal_source_region: str | None, builder: QpvQueryBuilder):
    return builder.get_total("groupings" if builder.groupby_colonne else "lignes")


class GetTotalOfLignes:
    """Service applicatif pour la récupération du total des lignes financières."""

    def __init__(self, builder: QpvQueryBuilder) -> None:
        self._builder = builder
        self._logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")

    def retrieve_total(
        self,
        params: QpvQueryParams,
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
