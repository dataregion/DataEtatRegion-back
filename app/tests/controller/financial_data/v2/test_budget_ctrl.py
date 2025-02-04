from unittest.mock import patch
from tests.controller.financial_data import patching_roles


def test_get_budget_with_themes(test_client):
    # Bug sur les theme avec ,
    themes = ["Thème avec, virgule", "Travail"]
    url = f"/financial-data/api/v2/budget?theme={'|'.join(themes)}&page_number=0&limit=100"
    with patching_roles(None), patch("app.controller.financial_data.v2.BudgetCtrls.search_lignes_budgetaires") as mock:
        response = test_client.get(url, follow_redirects=True)
        mock.assert_called_once_with(
            **{
                "page_number": 0,
                "limit": 100,
                "n_ej": None,
                "source": None,
                "code_programme": None,
                "niveau_geo": None,
                "code_geo": None,
                "ref_qpv": None,
                "code_qpv": None,
                "theme": ["Thème avec, virgule", "Travail"],
                "siret_beneficiaire": None,
                "types_beneficiaires": None,
                "annee": None,
                "centres_couts": None,
                "domaine_fonctionnel": None,
                "referentiel_programmation": None,
                "tags": None,
                "source_region": "053",
                "data_source": None,
            }
        )
        assert response.status_code == 204
