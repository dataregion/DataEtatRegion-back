import json
from unittest.mock import patch

import pytest

from app import db
from app.models.financial.FinancialAe import FinancialAe
from app.models.financial.FinancialCp import FinancialCp
from app.models.refs.siret import Siret
from app.tasks.financial import LineImportTechInfo
from app.tasks.financial.import_financial import import_file_cp_financial
from app.tasks.financial.import_financial import import_lines_financial_cp
from tests import TESTS_PATH

_chorus = TESTS_PATH / "data" / "chorus"
_chorus_split = _chorus / "split"


def _next_tech_info_fn():
    index = 0

    def _next_tech_info():
        nonlocal index
        index += 1
        return ("parent task id", index)

    return _next_tech_info


_next_tech_info = _next_tech_info_fn()


@pytest.fixture(scope="module", autouse=True)
def cleanup_after_tests():
    yield
    # Exécutez des actions nécessaires après tous les tests
    db.session.execute(db.delete(FinancialCp))
    db.session.execute(db.delete(FinancialAe))
    db.session.commit()


@patch("app.tasks.financial.import_financial._send_subtask_financial_cp")
def test_import_file_cp(mock_subtask):
    # DO
    with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
        import_file_cp_financial(_chorus_split / "financial_cp.csv", "35", 2023)

    # Vérifiez que la sous-tâche a été appelée le bon nombre de fois
    assert mock_subtask.call_count == 1

    # Vérifiez que la sous-tâche a été appelée avec les bons arguments
    expected_calls = [
        {
            "data": '{"programme":"101","domaine_fonctionnel":"0101-01","centre_couts":"BG00\\/DSJCARE035","referentiel_programmation":"BG00\\/010101010113","n_ej":"#","n_poste_ej":"#","n_dp":"500043027","date_base_dp":"31.12.2022","date_derniere_operation_dp":"25.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":"1001477845","fournisseur_paye_label":"SANS AE","siret":"84442098400016","compte_code":"PCE\\/6512300000","compte_budgetaire":"Transferts aux m\\u00e9nag","groupe_marchandise":"#","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N","montant":"28,26"}',
            "task": LineImportTechInfo(file_import_taskid=None, lineno=1),
        },
        {
            "data": '{"programme":"101","domaine_fonctionnel":"0101-01","centre_couts":"BG00\\/DSJCARE035","referentiel_programmation":"BG00\\/010101010113","n_ej":"#","n_poste_ej":"#","n_dp":"500043030","date_base_dp":"31.12.2022","date_derniere_operation_dp":"25.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":"1001273578","fournisseur_paye_label":"SANS AE","siret":"41867744900054","compte_code":"PCE\\/6512300000","compte_budgetaire":"Transferts aux m\\u00e9nag","groupe_marchandise":"#","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N","montant":"27,96"}',
            "task": LineImportTechInfo(file_import_taskid=None, lineno=2),
        },
        {
            "data": '{"programme":"152","domaine_fonctionnel":"0152-04-01","centre_couts":"BG00\\/GN5GDPL044","referentiel_programmation":"BG00\\/015234300101","n_ej":"2103105755","n_poste_ej":"5","n_dp":"100011636","date_base_dp":"25.12.2022","date_derniere_operation_dp":"18.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":"1400875965","fournisseur_paye_label":"AE EXIST","siret":"#","compte_code":"PCE\\/6113110000","compte_budgetaire":"D\\u00e9penses de fonction","groupe_marchandise":"36.01.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"S198063","montant":"252"}',
            "task": LineImportTechInfo(file_import_taskid=None, lineno=3),
        },
        {
            "data": '{"programme":"152","domaine_fonctionnel":"0152-04-01","centre_couts":"BG00\\/GN5GDPL044","referentiel_programmation":"BG00\\/015234300101","n_ej":"2103105755","n_poste_ej":"5","n_dp":"100011636","date_base_dp":"25.12.2022","date_derniere_operation_dp":"18.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":"1400875965","fournisseur_paye_label":"AE EXIST 2","siret":"#","compte_code":"PCE\\/6113110000","compte_budgetaire":"D\\u00e9penses de fonction","groupe_marchandise":"36.01.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"S198063","montant":"150"}',
            "task": LineImportTechInfo(file_import_taskid=None, lineno=4),
        },
        {
            "data": '{"programme":"152","domaine_fonctionnel":"0152-04-01","centre_couts":"BG00\\/GN5GDPL044","referentiel_programmation":"BG00\\/015234300101","n_ej":"2103105755","n_poste_ej":"1","n_dp":"100011552","date_base_dp":"25.12.2022","date_derniere_operation_dp":"18.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":"1001246979","fournisseur_paye_label":"AE NOT EXIST","siret":"45228173600010","compte_code":"PCE\\/6113110000","compte_budgetaire":"D\\u00e9penses de fonction","groupe_marchandise":"36.01.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N5244215","montant":"807,28"}',
            "task": LineImportTechInfo(file_import_taskid=None, lineno=5),
        },
    ]

    mock_subtask.assert_called_once_with(expected_calls, "35", 2023, 0)


def test_import_new_line_cp_without_ae(session):
    # GIVEN
    data = '{"programme":"101","domaine_fonctionnel":"0101-01","centre_couts":"BG00\\/DSJCARE035","referentiel_programmation":"BG00\\/010101010113","n_ej":"#","n_poste_ej":"#","n_dp":500043027,"date_base_dp":"31.12.2022","date_derniere_operation_dp":"25.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":1001477845,"fournisseur_paye_label":"SANS AE","siret":"84442098400016","compte_code":"PCE\\/6512300000","compte_budgetaire":"Transferts aux m\\u00e9nag","groupe_marchandise":"#","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N","montant":"28,26"}'

    # DO
    with patch(
        "app.services.siret.update_siret_from_api_entreprise",
        return_value=Siret(**{"code": "81412098400016", "code_commune": "35099"}),
    ):
        import_lines_financial_cp([{"data": data, "task": _next_tech_info()}], 0, "35", 2023)

        # ASSERT

    data = session.execute(db.select(FinancialCp).filter_by(n_dp="500043027")).scalar_one_or_none()
    assert data.id_ae is None
    assert data.annee == 2023
    assert data.programme == "101"
    assert data.n_poste_ej is None
    assert data.n_ej is None
    assert data.centre_couts == "DSJCARE035"
    assert data.referentiel_programmation == "010101010113"
    assert data.montant == 28.26


def test_import_new_line_cp_with_siret_empty(session):
    # GIVEN
    data = '{"programme":"102","domaine_fonctionnel":"0102-01","centre_couts":"BG00\\/DSJCARE035","referentiel_programmation":"BG00\\/010101010113","n_ej":"#","n_poste_ej":"#","n_dp":1222,"date_base_dp":"31.12.2022","date_derniere_operation_dp":"25.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":1001477845,"fournisseur_paye_label":"SANS AE","siret":"#","compte_code":"PCE\\/6512300000","compte_budgetaire":"Transferts aux m\\u00e9nag","groupe_marchandise":"#","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N","montant":"28,26"}'

    # DO
    import_lines_financial_cp([{"data": data, "task": _next_tech_info()}], 0, "35", 2023)

    # ASSERT
    data = session.execute(db.select(FinancialCp).filter_by(n_dp="1222")).scalar_one_or_none()
    assert data.id_ae is None
    assert data.siret is None


def test_import_new_line_cp_with_date_empty(session):
    # GIVEN
    data = '{"programme":"723","domaine_fonctionnel":"0723-13","centre_couts":"BG00\/FIP0000035","referentiel_programmation":"BG00\/072300010133","n_ej":"1405886249","n_poste_ej":"1","n_dp":"100004682","date_base_dp":"#","date_derniere_operation_dp":"12.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":"23455","fournisseur_paye_label":"XXXX","siret":"11111111111111","compte_code":"PCE\/6115450000","compte_budgetaire":"D\u00e9penses de fonction","groupe_marchandise":"37.02.04","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\u00e9","localisation_interministerielle":"LOCMIN","montant":"400,2"}'
    # DO
    with patch(
        "app.services.siret.update_siret_from_api_entreprise",
        return_value=Siret(**{"code": "11111111111111", "code_commune": "35099"}),
    ):
        import_lines_financial_cp([{"data": data, "task": _next_tech_info()}], 0, "35", 2023)

    # ASSERT
    data = session.execute(db.select(FinancialCp).filter_by(n_dp="100004682")).scalar_one_or_none()
    assert data.id_ae is None
    assert data.date_base_dp is None


def test_import_line_with_dp_exist(session):
    # GIVEN
    data_cp_exist = '{"programme":"723","domaine_fonctionnel":"0723-13","centre_couts":"BG00\/FIP0000035","referentiel_programmation":"BG00\/072300010133","n_ej":"1405886249","n_poste_ej":"1","n_dp":"12","date_base_dp":"#","date_derniere_operation_dp":"12.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":"23455","fournisseur_paye_label":"XXXX","siret":"2121212","compte_code":"PCE\/6115450000","compte_budgetaire":"D\u00e9penses de fonction","groupe_marchandise":"37.02.04","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\u00e9","localisation_interministerielle":"LOCMIN","montant":"400,2"}'
    data_new_cp = '{"programme":"723","domaine_fonctionnel":"0723-13","centre_couts":"BG00\/FIP0000035","referentiel_programmation":"BG00\/072300010133","n_ej":"1405886249","n_poste_ej":"2","n_dp":"12","date_base_dp":"#","date_derniere_operation_dp":"12.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":"23455","fournisseur_paye_label":"XXXX","siret":"2121212","compte_code":"PCE\/6115450000","compte_budgetaire":"D\u00e9penses de fonction","groupe_marchandise":"37.02.04","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\u00e9","localisation_interministerielle":"LOCMIN","montant":"400,2"}'
    financial_cp_1 = FinancialCp(json.loads(data_cp_exist), annee=2023, source_region="53")
    session.add(financial_cp_1)
    session.commit()

    # DO
    with patch(
        "app.services.siret.update_siret_from_api_entreprise",
        return_value=Siret(**{"code": "2121212", "code_commune": "35099"}),
    ):
        import_lines_financial_cp([{"data": data_new_cp, "task": _next_tech_info()}], 0, "35", 2023)

    # ASSERT
    data = session.execute(db.select(FinancialCp).filter_by(n_dp="12")).all()
    assert len(data) == 2


def test_import_new_line_cp_with_ae(session):
    # given
    data_cp = '{"programme":"152","domaine_fonctionnel":"0152-04-01","centre_couts":"BG00\\/GN5GDPL044","referentiel_programmation":"BG00\\/015234300101","n_ej":"2103105755","n_poste_ej":"5","n_dp":100011636,"date_base_dp":"25.12.2022","date_derniere_operation_dp":"18.01.2023","n_sf":"#","data_sf":"#","fournisseur_paye":"1400875965","fournisseur_paye_label":"AE EXIST","siret":"#","compte_code":"PCE\\/6113110000","compte_budgetaire":"D\\u00e9penses de fonction","groupe_marchandise":"36.01.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"S198063","montant":"252"}'
    data_ae = '{"annee":2002, "source_region":"53","programme":"152","domaine_fonctionnel":"0103-01-01","centre_couts":"BG00\\/DREETS0035","referentiel_programmation":"BG00\\/010300000108","n_ej":"2103105755","n_poste_ej":5,"date_modification_ej":"10.01.2023","fournisseur_titulaire":1001465507,"fournisseur_label":"ATLAS SOUTENIR LES COMPETENCES","siret":"85129663200017","compte_code":"PCE\\/6522800000","compte_budgetaire":"Transferts aux entre","groupe_marchandise":"09.02.01","contrat_etat_region":"#","contrat_etat_region_2":"Non affect\\u00e9","localisation_interministerielle":"N53","montant":"22500"}'
    financial_ae = FinancialAe(**json.loads(data_ae))
    session.add(financial_ae)
    session.commit()

    # DO
    with patch(
        "app.services.siret.update_siret_from_api_entreprise",
        return_value=Siret(**{"code": "00000002121212", "code_commune": "35099"}),
    ):
        import_lines_financial_cp([{"data": data_cp, "task": _next_tech_info()}], 0, "35", 2023)

    financial_cp = session.execute(db.select(FinancialCp).filter_by(n_dp="100011636")).scalar_one_or_none()
    assert financial_cp.id_ae == financial_ae.id
    assert financial_cp.annee == 2023
    assert financial_cp.programme == "152"
    assert financial_cp.n_poste_ej == 5
    assert financial_cp.n_ej == "2103105755"
    assert financial_cp.montant == 252
