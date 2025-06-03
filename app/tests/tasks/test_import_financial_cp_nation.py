from models.entities.refs.Region import Region
from models.entities.refs.Siret import Siret
import pytest

from models.entities.financial.FinancialAe import FinancialAe
from models.entities.financial.FinancialCp import FinancialCp
from models.entities.refs.CodeProgramme import CodeProgramme
from app.tasks.financial.import_financial import import_lines_financial_cp
from tests import delete_references
from tests.tasks.tags.test_tag_acv import get_or_create


@pytest.fixture(scope="module", autouse=True)
def cleanup_after_tests(database):
    yield
    # Exécutez des actions nécessaires après tous les tests
    database.session.execute(database.delete(FinancialCp))
    database.session.execute(database.delete(FinancialAe))
    database.session.commit()


def test_import_new_line_cp_nation(database, session):
    # GIVEN
    data = '{"programme":"0354","domaine_fonctionnel":"0354-02","centre_couts":"ADCSDAT076","referentiel_programmation":"035301010301","n_ej":"2104583353","n_poste_ej":"1","n_dp":"100379604","date_base_dp":"11\\/12\\/2024","date_derniere_operation_dp":"13\\/12\\/2024","fournisseur_paye":"1000972118","fournisseur_paye_label":"AGENCE NATIONALE DES TITRES","siret":"13000326200024","compte_code":"6541100000","compte_budgetaire":"64","groupe_marchandise":"12.01.01","contrat_etat_region":"","localisation_interministerielle":"N1175","montant":"100,18","exercice_comptable":"2024","n_poste_dp":"2","programme_doublon":"0354","tranche_fonctionnelle":"","fonds":"","projet_analytique":"","societe":"DILA","type_piece":"RE","data_source":"NATION","source_region":"00"}'

    # chorus = FinancialAe(**json.loads(data))
    get_or_create(session, Siret, code="13000326200024")
    get_or_create(session, Region, code="00")
    session.commit()
    # DO
    import_lines_financial_cp([{"data": data, "task": ("parent task id", 0)}], 0, None, 2025)

    # ASSERT
    cp = session.execute(database.select(FinancialCp).where(FinancialCp.n_dp == "100379604")).scalar_one_or_none()
    programme = session.execute(database.select(CodeProgramme).where(CodeProgramme.code == "354")).scalar_one_or_none()

    assert programme.id is not None
    assert programme.code == "354"

    assert cp.id is not None
    assert cp.id_ae is None
    assert cp.source_region == "00"
    assert cp.annee == 2025
    assert cp.n_ej == "2104583353"
    assert cp.programme == "354"
    assert cp.n_poste_ej == 1
    assert cp.centre_couts == "ADCSDAT076"
    assert cp.referentiel_programmation == "035301010301"
    assert cp.tranche_fonctionnelle is None
    assert cp.fonds is None
    assert cp.montant == 100.18
    assert cp.domaine_fonctionnel == "0354-02"
    assert cp.projet_analytique is None
    assert cp.societe == "DILA"
    assert cp.type_piece == "RE"
    assert cp.localisation_interministerielle == "N1175"
    assert cp.compte_budgetaire == "64"
    assert cp.exercice_comptable == "2024"

    delete_references(session)
