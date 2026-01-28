# from unittest.mock import patch

from models.entities.financial.FinancialAe import FinancialAe

# from models.entities.financial.QpvLieuAction import QpvLieuAction
# from app.tasks.financial.import_financial import import_file_qpv_lieu_action
from models.entities.refs import Qpv

# from psycopg import IntegrityError
import pytest
from tests.tasks.tags.test_tag_acv import add_references
from tests import TESTS_PATH
# from tests import delete_references

_data = TESTS_PATH / "data"


@pytest.fixture(scope="function")
def add_qpv_1(database):
    qpv_1 = Qpv(**{"code": "QN04417I", "label": "QPV Test 1"})
    database.session.add(qpv_1)
    database.session.commit()
    yield qpv_1
    database.session.execute(database.delete(Qpv))
    database.session.commit()


@pytest.fixture(scope="function")
def add_qpv_2(database):
    qpv_2 = Qpv(**{"code": "QN04405M", "label": "QPV Test 2"})
    database.session.add(qpv_2)
    database.session.commit()
    yield qpv_2
    database.session.execute(database.delete(Qpv))
    database.session.commit()


@pytest.fixture(scope="function")
def add_ae_1(database):
    ae_1 = FinancialAe(
        **{
            "programme": "103",
            "domaine_fonctionnel": "0103-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "BG00\\/010300000108",
            "n_ej": "2103609602",
            "date_replication": "10.01.2023",
            "n_poste_ej": 5,
            "date_modification_ej": "10.01.2023",
            "fournisseur_titulaire": "1001465507",
            "fournisseur_label": "ATLAS SOUTENIR LES COMPETENCES",
            "siret": "85129663200017",
            "compte_code": "PCE\\/6522800000",
            "compte_budgetaire": "Transferts aux entre",
            "groupe_marchandise": "09.02.01",
            "contrat_etat_region": "#",
            "contrat_etat_region_2": "Non affect\\u00e9",
            "localisation_interministerielle": "N53",
            "montant": "15000",
            "annee": 2023,
            "source_region": "35",
            "data_source": "REGION",
        }
    )
    add_references(ae_1, database.session, region="35")
    database.session.add(ae_1)
    database.session.commit()
    yield ae_1
    database.session.execute(database.delete(FinancialAe))
    database.session.commit()


@pytest.fixture(scope="function")
def add_ae_2(database):
    ae_2 = FinancialAe(
        **{
            "programme": "103",
            "domaine_fonctionnel": "0103-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "BG00\\/010300000108",
            "n_ej": "2103609601",
            "date_replication": "10.01.2023",
            "n_poste_ej": 5,
            "date_modification_ej": "10.01.2023",
            "fournisseur_titulaire": "1001465507",
            "fournisseur_label": "ATLAS SOUTENIR LES COMPETENCES",
            "siret": "85129663200017",
            "compte_code": "PCE\\/6522800000",
            "compte_budgetaire": "Transferts aux entre",
            "groupe_marchandise": "09.02.01",
            "contrat_etat_region": "#",
            "contrat_etat_region_2": "Non affect\\u00e9",
            "localisation_interministerielle": "N53",
            "montant": "15000",
            "annee": 2023,
            "source_region": "35",
            "data_source": "REGION",
        }
    )
    add_references(ae_2, database.session, region="35")
    database.session.add(ae_2)
    database.session.commit()
    yield ae_2
    database.session.execute(database.delete(FinancialAe))
    database.session.commit()


# TODO Refaire le test sur Prefect
# def test_import_file_qpv_lieu_action(app, database, session, add_qpv_1, add_qpv_2, add_ae_1, add_ae_2):
#     # DO
#     with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
#         import_file_qpv_lieu_action(_data / "qpv_lieu_action.csv")

#     # ASSERT
#     data = session.execute(database.select(QpvLieuAction)).all()
#     assert len(data) == 2

#     data: QpvLieuAction = session.execute(
#         database.select(QpvLieuAction).where(QpvLieuAction.n_ej == "2103609602")
#     ).scalar_one_or_none()
#     assert data.id is not None
#     assert data.code_qpv == "QN04417I"
#     assert data.ratio_montant == 5000

#     database.session.execute(database.delete(QpvLieuAction))
#     database.session.commit()
#     delete_references(session)
