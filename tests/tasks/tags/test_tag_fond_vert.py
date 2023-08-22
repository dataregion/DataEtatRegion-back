import pytest
from sqlalchemy import insert

from app.models.financial.FinancialAe import FinancialAe


@pytest.fixture(scope="module")
def financial_ae(test_db):
    data = [
        {
            "annee": 2020,
            "montant": "22500",
            "source_region": "35",
            "n_ej": "n_ej",
            "n_poste_ej": 5,
            "programme": "380",
            "domaine_fonctionnel": "0103-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "BG00\\/010300000108",
            "date_modification_ej": "10.01.2023",
            "fournisseur_titulaire": 1001465507,
            "fournisseur_label": "ATLAS SOUTENIR LES COMPETENCES",
            "siret": "85129663200017",
        }
    ]
    test_db.session.execute(insert(FinancialAe), data)
    test_db.session.commit()


def test_apply_fond_vert(test_db):
    # test
    print("oucou")
