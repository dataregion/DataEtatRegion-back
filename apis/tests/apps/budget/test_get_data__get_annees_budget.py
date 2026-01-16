import pytest
from apis.database import get_session_main
from services.shared.source_query_params import SourcesQueryParams
from apis.apps.budget.services.get_data import get_annees_budget


@pytest.mark.skip(
    reason="Sert d'exemple. Peut être réactivé lorsqu'on saura provisionner une bdd de test remplie."
)  # XXX
def test_get_annees_budget(test_db):
    session = next(get_session_main())
    params = SourcesQueryParams(source_region="053")
    _ = get_annees_budget(session, params=params)
