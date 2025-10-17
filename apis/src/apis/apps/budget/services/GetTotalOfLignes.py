from sqlalchemy.orm import Session

from apis.apps.budget.models.budget_query_params import FinancialLineQueryParams
from apis.apps.budget.services.query_builder import FinancialLineQueryBuilder


class GetTotalOfLignes:
    def __init__(self, db: Session, builder: FinancialLineQueryBuilder) -> None:
        self._db = db
        self._builder = builder

    def retrieve_total(
        self,
        params: FinancialLineQueryParams,
        additionnal_source_region: str | None = None,
    ):
        pass
    
def _cache_key(params: FinancialLineQueryParams, additionnal_source_region: str | None = None) -> str | None:
    """
    Calcule une clé de cache unique pour les paramètres donnés.
    Renvoie None si les paramètres ne sont pas cacheables.
    """
    cache_key = {
        "colonnes": params.colonnes,
        "source_region": params.source_region,
        "data_source": params.data_source,
        "filters": params.filters,
        "search": params.search,
        "fields_search": params.fields_search,
        "groupby_colonne": params.groupby_colonne,
        "additionnal_source_region": additionnal_source_region,
    }

    key = f"GetTotaleOfLignes-{params.cache_key()}"
    if additionnal_source_region:
        key += f"-{additionnal_source_region}"
    return key
