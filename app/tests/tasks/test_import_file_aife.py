from unittest.mock import call, patch
import json
from app.tasks.financial import LineImportTechInfo
import pytest

from models.entities.financial.FinancialAe import FinancialAe
from models.entities.financial.FinancialCp import FinancialCp
from app.tasks.files.file_task import read_csv_and_import_fichier_nat_ae_cp
from tests import TESTS_PATH


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
def test_fusion_ae_nat(mock_subtask):
    # DO
    with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
        read_csv_and_import_fichier_nat_ae_cp.run(
            _chorus_national / "aife_ae_double_ej.csv",
            _chorus_national / "aife_cp.csv",
            json.dumps({"sep": '";"', "skiprows": 0, "dtype": "str"}),
            2025,
        )

    mock_subtask.assert_has_calls(
        [
            call("import_lines_financial_cp"),
            call("import_lines_financial_ae"),
            # montant fusionné et suppression des montant à zero
            call().delay(
                [
                    '{"programme":"0102","domaine_fonctionnel":"0102-01","centre_couts":"EMPEF00075","referentiel_programmation":"010200000101","n_ej":"2104273645","date_replication":"25\\/01\\/2024","n_poste_ej":"4","date_modification_ej":"19\\/12\\/2024","fournisseur_titulaire":"0000000000","fournisseur_titulaire_label":"FOURNISSEUR_ANON","siret":"13000548100010","compte_code":"6512300000","compte_budgetaire":"61","groupe_marchandise":"07.02.05","contrat_etat_region":"","localisation_interministerielle":"N1175","montant":"138936678.56","centre_financier":"0102-CEFP-C001","tranche_fonctionnelle":"","axe_ministeriel_1":"Non affect\\u00e9","fonds":"","projet_analytique":"","axe_ministeriel_2":"","societe":"ADCE","data_source":"NATION","source_region":"00","annee":2025}',
                    '{"programme":"0102","domaine_fonctionnel":"0102-01","centre_couts":"EMPEF00075","referentiel_programmation":"010200000101","n_ej":"2104273645","date_replication":"25\\/01\\/2024","n_poste_ej":"1","date_modification_ej":"19\\/12\\/2024","fournisseur_titulaire":"0000000000","fournisseur_titulaire_label":"FOURNISSEUR_ANON","siret":"13000548100010","compte_code":"6512300000","compte_budgetaire":"61","groupe_marchandise":"07.02.05","contrat_etat_region":"","localisation_interministerielle":"N1175","montant":"1200.0","centre_financier":"0102-CEFP-C001","tranche_fonctionnelle":"","axe_ministeriel_1":"Non affect\\u00e9","fonds":"","projet_analytique":"","axe_ministeriel_2":"","societe":"ADCE","data_source":"NATION","source_region":"00","annee":2025}',
                ],
                None,
                2025,
                0,
                [],
            ),
            call().delay(
                [
                    {
                        "data": '{"programme":"0354","domaine_fonctionnel":"0354-02","centre_couts":"ADCSDAT075","referentiel_programmation":"035401010301","n_ej":"2104583353","n_poste_ej":"1","n_dp":"100379604","date_base_dp":"11\\/12\\/2024","date_derniere_operation_dp":"13\\/12\\/2024","fournisseur_paye":"1000972118","fournisseur_paye_label":"AGENCE NATIONALE DES TITRES","siret":"13000326200024","compte_code":"6541100000","compte_budgetaire":"64","groupe_marchandise":"12.01.01","contrat_etat_region":"","localisation_interministerielle":"N1175","montant":"9159575,18","exercice_comptable":"2024","n_poste_dp":"2","programme_doublon":"0354","tranche_fonctionnelle":"","fonds":"","projet_analytique":"","societe":"ADCE","type_piece":"RE","data_source":"NATION","source_region":"00"}',
                        "task": LineImportTechInfo(file_import_taskid=None, lineno=1),
                    },
                    {
                        "data": '{"programme":"0354","domaine_fonctionnel":"0354-02","centre_couts":"ADCSDAT075","referentiel_programmation":"035401010301","n_ej":"2104453606","n_poste_ej":"1","n_dp":"100241599","date_base_dp":"09\\/08\\/2024","date_derniere_operation_dp":"09\\/08\\/2024","fournisseur_paye":"1000972118","fournisseur_paye_label":"AGENCE NATIONALE DES TITRES","siret":"13000326200024","compte_code":"6541100000","compte_budgetaire":"64","groupe_marchandise":"12.01.01","contrat_etat_region":"","localisation_interministerielle":"N1175","montant":"12615940,52","exercice_comptable":"2024","n_poste_dp":"2","programme_doublon":"0354","tranche_fonctionnelle":"","fonds":"","projet_analytique":"","societe":"ADCE","type_piece":"RE","data_source":"NATION","source_region":"00"}',
                        "task": LineImportTechInfo(file_import_taskid=None, lineno=0),
                    },
                ],
                0,
                None,
                2025,
            ),
        ],
        any_order=True,
    )

    assert 2 == mock_subtask.call_count


@patch("app.tasks.financial.import_financial.subtask")
def test_split_file_aife(mock_subtask):
    # DO
    with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
        read_csv_and_import_fichier_nat_ae_cp.run(
            _chorus_national / "aife_ae.csv",
            _chorus_national / "aife_cp.csv",
            json.dumps({"sep": '";"', "skiprows": 0, "dtype": "str"}),
            2024,
        )

    mock_subtask.assert_has_calls(
        [
            call("import_lines_financial_cp"),
            call("import_lines_financial_ae"),
            call().delay(
                [
                    '{"programme":"0354","domaine_fonctionnel":"0354-02","centre_couts":"ADCSDAT075","referentiel_programmation":"035401010301","n_ej":"2104583353","date_replication":"10\\/12\\/2024","n_poste_ej":"1","date_modification_ej":"10\\/12\\/2024","fournisseur_titulaire":"1000972118","fournisseur_titulaire_label":"AGENCE; NATIONALE \\"\\"DES TITRES\\"\\"","siret":"13000326200024","compte_code":"6541100000","compte_budgetaire":"64","groupe_marchandise":"12.01.01","contrat_etat_region":"1","localisation_interministerielle":"N1175","montant":"9159575.18","centre_financier":"0354-CDMA-CDAT","tranche_fonctionnelle":"","axe_ministeriel_1":"","fonds":"","projet_analytique":"","axe_ministeriel_2":"","societe":"ADCE","data_source":"NATION","source_region":"00","annee":2024}',
                    '{"programme":"0354","domaine_fonctionnel":"0354-02","centre_couts":"ADCSDAT075","referentiel_programmation":"035401010301","n_ej":"2104453606","date_replication":"08\\/08\\/2024","n_poste_ej":"1","date_modification_ej":"08\\/08\\/2024","fournisseur_titulaire":"1000972118","fournisseur_titulaire_label":"XXX \\"\\";P BBB\\"\\"","siret":"13000326200024","compte_code":"6541100000","compte_budgetaire":"64","groupe_marchandise":"12.01.01","contrat_etat_region":"","localisation_interministerielle":"N1175","montant":"12615940.52","centre_financier":"0354-CDMA-CDAT","tranche_fonctionnelle":"","axe_ministeriel_1":"","fonds":"","projet_analytique":"","axe_ministeriel_2":"","societe":"BRET","data_source":"NATION","source_region":"53","annee":2024}',
                ],
                None,
                2024,
                0,
                [
                    {
                        "data": '{"programme":"0354","domaine_fonctionnel":"0354-02","centre_couts":"ADCSDAT075","referentiel_programmation":"035401010301","n_ej":"2104583353","n_poste_ej":"1","n_dp":"100379604","date_base_dp":"11\\/12\\/2024","date_derniere_operation_dp":"13\\/12\\/2024","fournisseur_paye":"1000972118","fournisseur_paye_label":"AGENCE NATIONALE DES TITRES","siret":"13000326200024","compte_code":"6541100000","compte_budgetaire":"64","groupe_marchandise":"12.01.01","contrat_etat_region":"","localisation_interministerielle":"N1175","montant":"9159575,18","exercice_comptable":"2024","n_poste_dp":"2","programme_doublon":"0354","tranche_fonctionnelle":"","fonds":"","projet_analytique":"","societe":"ADCE","type_piece":"RE","data_source":"NATION","source_region":"00"}',
                        "task": LineImportTechInfo(file_import_taskid=None, lineno=1),
                    }
                ],
            ),
        ],
        any_order=True,
    )

    assert 2 == mock_subtask.call_count
