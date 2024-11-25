from unittest.mock import patch
import json

import pytest

from models.entities.financial.FinancialAe import FinancialAe
from models.entities.financial.FinancialCp import FinancialCp
from models.entities.refs.CodeProgramme import CodeProgramme
from models.entities.refs.Region import Region
from models.entities.refs.Siret import Siret
from app.tasks.files.file_task import read_csv_and_import_ae_cp, read_csv_and_import_fichier_nat_ae_cp
from app.tasks.financial.import_financial import import_lines_financial_ae
from tests import TESTS_PATH, delete_references
from tests.tasks.tags.test_tag_acv import add_references, get_or_create


@pytest.fixture(scope="module", autouse=True)
def cleanup_after_tests(database):
    yield
    # Exécutez des actions nécessaires après tous les tests
    database.session.execute(database.delete(FinancialCp))
    database.session.execute(database.delete(FinancialAe))
    database.session.commit()


_chorus = TESTS_PATH / "data" / "chorus"
_chorus_national = _chorus / "national"


@patch("app.tasks.financial.import_financial.subtask")
def test_split_csv_and_import_ae_and_cp(mock_subtask):
    # DO
    with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
        read_csv_and_import_ae_cp(
            _chorus / "chorus_ae.csv", _chorus / "financial_cp.csv", json.dumps({"sep": ",", "skiprows": 8}), "32", 2022
        )
    assert 2 == mock_subtask.call_count


@patch("app.tasks.financial.import_financial.subtask")
def test_split_csv_and_import_fichier_nat_ae_cp(mock_subtask):
    # DO
    with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
        read_csv_and_import_fichier_nat_ae_cp(
            _chorus_national / "ej_data_etat_quot_2024-09-26.csv",
            _chorus_national / "dp_data_etat_quot_2024-09-26.csv",
            json.dumps({"sep": "|", "skiprows": 0, "keep_default_na": False, "na_values": [], "dtype": "str"}),
        )
    assert 9 == mock_subtask.call_count


def test_import_new_line_ae(database, session):
    # AJout Somme positive
    data = '{"date_replication":"10.01.2023","montant":"22500,12","annee":2023,"source_region":"35","n_ej":"2103105755","n_poste_ej":5,"programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"85129663200117","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source":"REGION"}'
    # DO
    add_references(FinancialAe(**json.loads(data)), session, region="35")

    import_lines_financial_ae([data], "35", 2023, 0, [])

    # ASSERT
    data = session.execute(database.select(FinancialAe).where(FinancialAe.n_ej == "2103105755")).scalar_one_or_none()
    programme = session.execute(database.select(CodeProgramme).where(CodeProgramme.code == "103")).scalar_one_or_none()

    assert programme.id is not None
    assert programme.code == "103"

    assert data.id is not None
    assert data.annee == 2023
    assert data.n_poste_ej == 5
    assert data.centre_couts == "DREETS0035"
    assert data.referentiel_programmation == "010300000108"
    assert len(data.montant_ae) == 1
    assert data.montant_ae[0].montant == 22500.12
    assert data.montant_ae[0].annee == 2023

    delete_references(session)


def test_import_lines_ae_with_duplicate_key(database, session):
    data = '{"date_replication":"10.01.2023","montant":"22500,12","annee":2023,"source_region":"35","n_ej":"2103105755","n_poste_ej":5,"programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"85129663200017","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source":"REGION"}'
    # DO
    add_references(FinancialAe(**json.loads(data)), session, region="35")

    import_lines_financial_ae(
        [
            '{"programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","n_ej":"2103105755","date_replication":"10.01.2023","n_poste_ej":5,"date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"85129663200017","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53","montant":"22500,12","annee":2023,"source_region":"35", "data_source":"REGION"}',
            '{"programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","n_ej":"2103105755","date_replication":"10.01.2023","n_poste_ej":5,"date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"85129663200017","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53","montant":"15000","annee":2023,"source_region":"35", "data_source":"REGION"}',
            '{"programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","n_ej":"2103105755","date_replication":"10.01.2023","n_poste_ej":5,"date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"NOT FOUND","siret":"#","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53","montant":"15000","annee":2023,"source_region":"35", "data_source":"REGION"}',
        ],
        "35",
        2023,
        0,
        [],
    )

    # ASSERT
    data = session.execute(database.select(FinancialAe).where(FinancialAe.n_ej == "2103105755")).scalar_one_or_none()
    programme = session.execute(database.select(CodeProgramme).where(CodeProgramme.code == "103")).scalar_one_or_none()

    assert programme.id is not None
    assert programme.code == "103"

    assert data.id is not None
    assert data.annee == 2023
    assert data.n_poste_ej == 5
    assert data.centre_couts == "DREETS0035"
    assert data.referentiel_programmation == "010300000108"
    assert len(data.montant_ae) == 1
    assert data.montant_ae[0].annee == 2023
    assert data.montant_ae[0].montant == 15000

    delete_references(session)


def test_import_lines_ae_with_duplicate_ref(database, session):
    data = '{"montant":"22500,12","siret": "57202862900275", "annee":2023,"source_region":"35"}'
    # DO
    add_references(FinancialAe(**json.loads(data)), session, region="11")

    import_lines_financial_ae(
        [
            '{"domaine_fonctionnel": "0216-05-06", "centre_couts": "ADCAIAC075", "referentiel_programmation": "021606010402", "n_ej": "1000176402", "n_poste_ej": 17, "siret": "57202862900275", "compte_budgetaire": "51", "groupe_marchandise": "16.05.02", "contrat_etat_region": "", "localisation_interministerielle": "N1175", "annee": "2023", "montant": 39240.0, "source_region": "11", "programme": "0216", "data_source": "NATION"}',
            '{"domaine_fonctionnel": "0216-05-11", "centre_couts": "PN50000033", "referentiel_programmation": "021606040101", "n_ej": "1600073826", "n_poste_ej": 12, "siret": "57202862900275", "compte_budgetaire": "51", "groupe_marchandise": "36.05.08", "contrat_etat_region": "", "localisation_interministerielle": "B223939", "annee": "2023", "montant": 64.7, "source_region": "11", "programme": "0216", "data_source": "NATION"}',
            '{"domaine_fonctionnel": "0216-10-05", "centre_couts": "PRFDCAB053", "referentiel_programmation": "0216081008A5", "n_ej": "2104384696", "n_poste_ej": 1, "siret": "57202862900275", "compte_budgetaire": "63", "groupe_marchandise": "10.03.01", "contrat_etat_region": "", "localisation_interministerielle": "N5253", "annee": "2024", "montant": 650.0, "source_region": "11", "programme": "0216", "data_source": "NATION"}',
            '{"domaine_fonctionnel": "0216-05-06", "centre_couts": "ADCAIAC075", "referentiel_programmation": "021606010402", "n_ej": "1000176402", "n_poste_ej": 14, "siret": "57202862900275", "compte_budgetaire": "51", "groupe_marchandise": "16.05.02", "contrat_etat_region": "", "localisation_interministerielle": "N1175", "annee": "2023", "montant": 108480.0, "source_region": "11", "programme": "0216", "data_source": "NATION"}',
            '{"domaine_fonctionnel": "0216-05-06", "centre_couts": "ADCAIAC075", "referentiel_programmation": "021606010402", "n_ej": "1000176402", "n_poste_ej": 11, "siret": "57202862900275", "compte_budgetaire": "51", "groupe_marchandise": "16.05.02", "contrat_etat_region": "", "localisation_interministerielle": "N1175", "annee": "2023", "montant": 99480.0, "source_region": "11", "programme": "0216", "data_source": "NATION"}',
            '{"domaine_fonctionnel": "0216-03-05", "centre_couts": "MI5ZSIC059", "referentiel_programmation": "021603040101", "n_ej": "1512722596", "n_poste_ej": 1, "siret": "57202862900275", "compte_budgetaire": "51", "groupe_marchandise": "33.03.08", "contrat_etat_region": "", "localisation_interministerielle": "N32", "annee": "2024", "montant": 30838.72, "source_region": "11", "programme": "0216", "data_source": "NATION"}',
            '{"domaine_fonctionnel": "0216-05-11", "centre_couts": "PN50000033", "referentiel_programmation": "021606040101", "n_ej": "1600073826", "n_poste_ej": 10, "siret": "57202862900275", "compte_budgetaire": "51", "groupe_marchandise": "36.05.08", "contrat_etat_region": "", "localisation_interministerielle": "B223939", "annee": "2023", "montant": 27823.2, "source_region": "11", "programme": "0216", "data_source": "NATION"}',
            '{"domaine_fonctionnel": "0216-05-06", "centre_couts": "ADCAIAC075", "referentiel_programmation": "021606010402", "n_ej": "1000176402", "n_poste_ej": 2, "siret": "57202862900275", "compte_budgetaire": "51", "groupe_marchandise": "16.05.02", "contrat_etat_region": "", "localisation_interministerielle": "N1175", "annee": "2023", "montant": 133440.0, "source_region": "11", "programme": "0216", "data_source": "NATION"}',
        ],
        None,
        None,
        50,
        [],
    )

    # ASSERT
    programme = session.execute(database.select(CodeProgramme).where(CodeProgramme.code == "216")).scalar_one_or_none()

    assert programme.id is not None
    assert programme.code == "216"

    delete_references(session)


class _TestTriggeredException(Exception):
    """Exception personnalisée pour le test qui suit"""

    pass


def test_import_new_line_ae_with_commit_fail(database, session):
    # Données pour le test
    data = '{"date_replication":"10.01.2023","montant":"22500,12","annee":2023,"source_region":"35","n_ej":"2103105756","n_poste_ej":5,"programme":"303","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"85129663200018","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source":"REGION"}'
    # add_references(FinancialAe(**json.loads(data)), session, region="35")
    get_or_create(session, Region, code="35")
    session.commit()
    # Simulation du siret
    with patch(
        "app.services.siret.update_siret_from_api_entreprise",
        return_value=Siret(**{"code": "85129663200018", "code_commune": "35099"}),
    ):
        # Simulation d'une exception lors du commit
        with patch(
            "app.tasks.financial.import_financial._import_lines_financial_ae__before_commit_aes",
            side_effect=_TestTriggeredException("Une exception artificielle avant de sauvegarder le bulk d'AE"),
        ):
            with pytest.raises(_TestTriggeredException):
                import_lines_financial_ae([data, data, data], "35", 2023, 0, [])

    # Vérification qu'aucune donnée n'a été effectivement insérée dans la base de données
    data = session.execute(database.select(FinancialAe).where(FinancialAe.n_ej == "2103105756")).scalar_one_or_none()
    assert data is None

    programme = session.execute(database.select(CodeProgramme).where(CodeProgramme.code == "303")).scalar_one_or_none()
    assert programme is None
    delete_references(session)


def test_import_changing_ref(database, session):
    # Données pour le test
    data_wout_siret = '{"date_replication":"10.01.2023","montant":"22500,12","annee":2023,"source_region":"35","n_ej":"2103105756","n_poste_ej":5,"programme":"303","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"#","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source":"REGION"}'
    data_w_siret = '{"date_replication":"10.01.2023","montant":"22500,12","annee":2023,"source_region":"35","n_ej":"2103105756","n_poste_ej":5,"programme":"303","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"85129663200018","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source":"REGION"}'

    get_or_create(session, Region, code="35")

    session.commit()

    # Simulation du siret
    with patch(
        "app.services.siret.update_siret_from_api_entreprise",
        return_value=Siret(**{"code": "85129663200018", "code_commune": "35099"}),
    ):
        import_lines_financial_ae([data_wout_siret, data_wout_siret, data_w_siret], "35", 2023, 0, [])

    # Vérification que le siret a été inséré
    siret = session.execute(database.select(Siret)).scalar_one_or_none()
    assert siret is not None, "Le siret doit être inseré."

    delete_references(session)


def test_import_update_line_montant_positive_ae(database, session):
    # WHEN
    data = '{"annee":2020,"montant":"22500","source_region":"35","n_ej":"ej_to_update","n_poste_ej":5,"programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire": "1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"85129663200017","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source" : "REGION"}'
    chorus = FinancialAe(**json.loads(data))
    add_references(chorus, session, region="35")
    session.add(chorus)
    session.commit()

    # update data, same n_ej n_poste_ej
    data_update = '{"annee":2021,"montant":10000,"source_region":"35","n_ej":"ej_to_update","n_poste_ej":5,"programme":"NEW","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.02.2023","fournisseur_titulaire": "1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000171","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"UPDATE","localisation_interministerielle":"N53", "data_source":"REGION"}'
    add_references(FinancialAe(**json.loads(data_update)), session, region="35")

    # DO
    import_lines_financial_ae([data_update], "35", 2021, 0, [])

    data = session.execute(database.select(FinancialAe).where(FinancialAe.n_ej == "ej_to_update")).scalar_one_or_none()
    assert data.id == chorus.id
    assert data.annee == 2021
    assert data.n_poste_ej == 5
    assert data.centre_couts == "DREETS0035"
    assert data.programme == "NEW"
    assert data.referentiel_programmation == "010300000108"
    assert len(data.montant_ae) == 1
    assert data.montant_ae[0].annee == 2021
    assert data.montant_ae[0].montant == 10000
    delete_references(session)


def test_import_montant_negatif(database, session):
    # WHEN - ligne AE sur année n-1 avec montant > 0
    data = '{"annee":2021,"source_region":"35","montant":22500,"n_ej":"ej_negatif","n_poste_ej":6,"programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000172","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source" : "REGION"}'
    chorus = FinancialAe(**json.loads(data))
    add_references(chorus, session, region="35")
    session.add(chorus)
    session.commit()

    # update data, avec montant < 0
    data_update = '{"annee":2022,"montant":-105.50,"n_ej":"ej_negatif","n_poste_ej":6,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000172","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source":"REGION"}'

    # DO
    import_lines_financial_ae([data_update], "35", 2022, 0, [])

    data = session.execute(database.select(FinancialAe).filter_by(n_ej="ej_negatif")).scalar_one_or_none()
    assert data.id == chorus.id
    assert data.annee == 2021
    assert data.n_poste_ej == 6
    assert len(data.montant_ae) == 2
    assert data.montant_ae[0].montant == 22500
    assert data.montant_ae[1].montant == -105.50
    delete_references(session)


def test_import_montant_negatif_sur_annee_anterieur(database, session):
    # WHEN - ligne AE sur année 2024 avec montant > 0
    data = '{"annee":2024,"montant":22500,"n_ej":"ej_negatif_2024","n_poste_ej":7,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000173","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source" : "REGION"}'
    chorus = FinancialAe(**json.loads(data))
    add_references(chorus, session, region="35")
    session.add(chorus)
    session.commit()

    # update data, avec montant < 0 sur année antérieur (normalement cas pas possible)
    data_update = '{"annee":2022,"montant":-105.50,"n_ej":"ej_negatif_2024","n_poste_ej":7,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000173","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source":"REGION"}'

    # DO
    import_lines_financial_ae([data_update], "35", 2022, 0, [])

    data = session.execute(database.select(FinancialAe).filter_by(n_ej="ej_negatif_2024")).scalar_one_or_none()
    assert data.id == chorus.id
    assert data.annee == 2024
    assert data.n_poste_ej == 7
    assert len(data.montant_ae) == 2
    assert data.montant_ae[0].montant == 22500
    assert data.montant_ae[1].montant == -105.50
    delete_references(session)


def test_import_deux_montant_negatif(database, session):
    # WHEN - ligne AE sur année 2024 avec montant > 0
    data = '{"annee":2020,"montant":100,"n_ej":"init_positif","n_poste_ej":7,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000174","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source" : "REGION"}'
    chorus = FinancialAe(**json.loads(data))
    add_references(chorus, session, region="35")
    session.add(chorus)
    session.commit()

    # update data, avec montant < 0 sur année antérieur (normalement cas pas possible)
    data_montant_2021 = '{"annee":2021,"montant":-5.50,"n_ej":"init_positif","n_poste_ej":7,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000174","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source":"REGION"}'
    data_montant_2022 = '{"annee":2022,"montant":-2.50,"n_ej":"init_positif","n_poste_ej":7,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000175","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source":"REGION"}'

    # DO
    add_references(FinancialAe(**json.loads(data_montant_2021)), session, region="35")
    add_references(FinancialAe(**json.loads(data_montant_2022)), session, region="35")
    import_lines_financial_ae([data_montant_2021], "35", 2021, 0, [])
    import_lines_financial_ae([data_montant_2022], "35", 2022, 0, [])

    data = session.execute(database.select(FinancialAe).filter_by(n_ej="init_positif")).first()[0]
    assert data
    assert data.id == chorus.id
    assert data.annee == 2020
    assert data.n_poste_ej == 7
    assert len(data.montant_ae) == 3
    montant_100, montant_moins_5, mointant_moins_2 = data.montant_ae
    assert montant_100.montant == 100
    assert montant_moins_5.montant == -5.50
    assert mointant_moins_2.montant == -2.50
    delete_references(session)


def test_import_montant_positif_apres_negatif_meme_annee(database, session):
    # WHEN - ligne AE sur année 2024 avec montant > 0
    data = '{"annee":2021,"montant":-102,"n_ej":"ej_negatif_2021","n_poste_ej":2,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000180","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source" : "REGION"}'
    chorus = FinancialAe(**json.loads(data))
    add_references(chorus, session, region="35")
    session.add(chorus)
    session.commit()  # pour avoir l'id

    # update data, avec montant > 0 sur année antérieur
    data_update = '{"annee":2021,"montant":500,"n_ej":"ej_negatif_2021","n_poste_ej":2,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000180","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source":"REGION"}'

    # DO
    import_lines_financial_ae([data_update], "35", 2021, 0, [])

    data = session.execute(database.select(FinancialAe).where(FinancialAe.n_ej == "ej_negatif_2021")).first()[0]
    assert data.id == chorus.id
    assert data.annee == 2021
    assert data.n_poste_ej == 2
    assert len(data.montant_ae) == 1
    assert data.montant_ae[0].montant == 500  # on ne conserve que le positif
    delete_references(session)


def test_import_montant_positif_apres_negatif_annee_differente(database, session):
    # WHEN - ligne AE sur année 2020 avec montant < 0
    data = '{"annee":2020,"montant":-0.1,"n_ej":"ej_negatif_2020","n_poste_ej":1,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000181","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source" : "REGION"}'
    chorus = FinancialAe(**json.loads(data))
    add_references(chorus, session, region="35")
    session.add(chorus)
    session.commit()

    # update data, avec montant > 0
    data_update = '{"annee":2021,"montant":500,"n_ej":"ej_negatif_2020","n_poste_ej":1,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"851296632000181","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53", "data_source" : "REGION"}'

    # DO
    import_lines_financial_ae([data_update], "35", 2021, 0, [])

    data = session.execute(database.select(FinancialAe).filter_by(n_ej="ej_negatif_2020")).first()[0]
    assert data.id == chorus.id
    assert data.annee == 2021
    assert data.n_poste_ej == 1
    assert len(data.montant_ae) == 2
    montant_ae_2020, montant_ae_2021 = data.montant_ae
    assert montant_ae_2020.montant == -0.1
    assert montant_ae_2020.annee == 2020
    assert montant_ae_2021.montant == 500
    assert montant_ae_2021.annee == 2021
    delete_references(session)


def test_import_line_missing_zero_siret(database, session):
    data = '{"annee":2023,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","n_ej":"siret_ej","n_poste_ej":5,"date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"6380341500023","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53","montant":22500, "data_source":"REGION"}'
    add_references(FinancialAe(**json.loads(data)), session, region="35")
    import_lines_financial_ae([data], "35", 2023, 0, [])

    # ASSERT
    data = session.execute(database.select(FinancialAe).filter_by(n_ej="siret_ej")).scalar_one_or_none()
    assert data.siret == "06380341500023"
    delete_references(session)


def test_import_new_line_ae_with_siret_empty(database, session):
    # GIVEN
    data = '{"annee":2023,"source_region":"35","programme":"103","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","n_ej":"siret_empty","n_poste_ej":5,"date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"#","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53","montant":22500, "data_source":"REGION"}'
    add_references(FinancialAe(**json.loads(data)), session, region="35")
    # DO
    import_lines_financial_ae([data], "35", 2023, 0, [])

    # ASSERT
    data = session.execute(database.select(FinancialAe).filter_by(n_ej="siret_empty")).scalar_one_or_none()
    assert data.siret is None
    delete_references(session)


def test_import_new_line_ae_with_cp(database, session):
    # GIVEN
    code_region = "53"

    source_region = Region()
    source_region.code = code_region
    source_region.label = "Ta région"

    n_ej = "11548315"
    data_cp_1 = (
        '{"programme":"152","domaine_fonctionnel":"0152-04-01","centre_couts":"BG00\\/GN5GDPL044","referentiel_programmation":"BG00\\/015234300101","n_ej":"'
        + n_ej
        + '","n_poste_ej":"5","n_dp":1,"date_base_dp":"25.12.2022","date_derniere_operation_dp":"18.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":"1400875965","fournisseur_paye_label":"AE EXIST","siret":"#","compte_code":"PCE\\/6113110000","compte_budgetaire":"D\\u00e9penses de fonction","groupe_marchandise":"36.01.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"S198063","montant":"252", "data_source":"REGION"}'
    )
    data_cp_2 = (
        '{"programme":"152","domaine_fonctionnel":"0152-04-01","centre_couts":"BG00\\/GN5GDPL044","referentiel_programmation":"BG00\\/015234300101","n_ej":"'
        + n_ej
        + '","n_poste_ej":"5","n_dp":2,"date_base_dp":"25.12.2022","date_derniere_operation_dp":"20.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":"1400875965","fournisseur_paye_label":"AE EXIST","siret":"#","compte_code":"PCE\\/6113110000","compte_budgetaire":"D\\u00e9penses de fonction","groupe_marchandise":"36.01.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"S198063","montant":"100", "data_source":"REGION"}'
    )
    data_ae = (
        '{"annee":2023,"source_region":"53","programme":"152","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","n_ej":"'
        + n_ej
        + '","n_poste_ej":5,"date_modification_ej":"10.01.2023","fournisseur_titulaire":"1001465507","fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"85129663200017","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53","montant":22500, "data_source":"REGION"}'
    )

    session.add(source_region)
    add_references(FinancialAe(**json.loads(data_ae)), session, region=code_region)

    # DO
    with patch(
        "app.services.siret.update_siret_from_api_entreprise",
        return_value=Siret(**{"code": "84442098400016", "code_commune": "35099"}),
    ):
        import_lines_financial_ae(
            [data_ae],
            code_region,
            2023,
            0,
            [{"data": data_cp_1, "task": ("task_id", 0)}, {"data": data_cp_2, "task": ("task_id", 1)}],
        )

        financial_ae = session.execute(
            database.select(FinancialAe).filter_by(n_ej=n_ej, n_poste_ej=5)
        ).scalar_one_or_none()
        financial_cp_1 = session.execute(
            database.select(FinancialCp).filter_by(n_ej=n_ej, n_poste_ej=5, montant=252.0)
        ).scalar_one_or_none()
        financial_cp_2 = session.execute(
            database.select(FinancialCp).filter_by(n_ej=n_ej, n_poste_ej=5, montant=100.0)
        ).scalar_one_or_none()
        # Check lien ae <-> cp
        assert financial_cp_1.id_ae == financial_ae.id
        assert financial_cp_2.id_ae == financial_ae.id
        delete_references(session)
