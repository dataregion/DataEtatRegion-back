from apis.config.current import get_config
from services.utilities.observability import cache_stats

from apis.apps.budget.models.budget_query_params import FinancialLineQueryParams
from apis.apps.budget.services.query_builder import FinancialLineQueryBuilder

from cachetools import cached, LRUCache
from cachetools.keys import hashkey

total_cache = LRUCache(maxsize=get_config().cache_config.budget_totaux_size)

def _cache_key(params: FinancialLineQueryParams, additionnal_source_region: str | None, builder: FinancialLineQueryBuilder):
    """
    Calcule une clé de cache unique pour les paramètres donnés.
    Renvoie None si les paramètres ne sont pas cacheables.
    """
    params_cache_key = params.get_total_cache_key()
    key = ("GetTotalOfLignes",params_cache_key,additionnal_source_region,) if params_cache_key is not None else None

    return hashkey(key)

@cache_stats()
@cached(total_cache, key=_cache_key, info=True)
def _cached_retrieve(params: FinancialLineQueryParams, additionnal_source_region: str | None, builder: FinancialLineQueryBuilder):
    return _retrieve(params, additionnal_source_region, builder)

def _retrieve(params: FinancialLineQueryParams, additionnal_source_region: str | None, builder: FinancialLineQueryBuilder):
    return builder.get_total("groupings" if builder.groupby_colonne else "lignes")

class GetTotalOfLignes:
    """Service applicatif pour la récupération du total des lignes financières."""
    def __init__(self, builder: FinancialLineQueryBuilder) -> None:
        self._builder = builder

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
            result = _cached_retrieve(params, additionnal_source_region, self._builder)

        return result
    
    
    
