from models.entities.refs.Region import Region
from models.entities.refs.Siret import Siret
import pytest

from models.entities.financial.FinancialAe import FinancialAe
from models.entities.financial.FinancialCp import FinancialCp
from models.entities.refs.CodeProgramme import CodeProgramme
from app.tasks.financial.import_financial import import_lines_financial_ae
from tests import delete_references
from tests.tasks.tags.test_tag_acv import get_or_create


@pytest.fixture(scope="module", autouse=True)
def cleanup_after_tests(database):
    yield
    # Exécutez des actions nécessaires après tous les tests
    database.session.execute(database.delete(FinancialCp))
    database.session.execute(database.delete(FinancialAe))
    database.session.commit()


def test_import_new_line_ae_nation(database, session):
    # GIVEN
    data = '{"programme":"0354","domaine_fonctionnel":"0354-02","centre_couts":"ADCSDAT075","referentiel_programmation":"035401010301","n_ej":"2104583353","date_replication":"10\\/12\\/2024","n_poste_ej":"1","date_modification_ej":"10\\/12\\/2024","fournisseur_titulaire":"1000972118","fournisseur_titulaire_label":"AGENCE NATIONALE DES TITRES","siret":"13000326200024","compte_code":"6541100000","compte_budgetaire":"64","groupe_marchandise":"12.01.01","contrat_etat_region":"","localisation_interministerielle":"N1175","montant":"9159575,18","centre_financier":"0354-CDMA-CDAT","tranche_fonctionnelle":"","axe_ministeriel_1":"","fonds":"","projet_analytique":"","axe_ministeriel_2":"","societe":"BRET","data_source":"NATION","source_region":53,"annee":2024}'

    # chorus = FinancialAe(**json.loads(data))
    get_or_create(session, Siret, code="13000326200024")
    get_or_create(session, Region, code="53")
    session.commit()
    # DO
    import_lines_financial_ae([data], None, 2024, 0, None)

    # ASSERT
    ae = session.execute(database.select(FinancialAe).where(FinancialAe.n_ej == "2104583353")).scalar_one_or_none()
    programme = session.execute(database.select(CodeProgramme).where(CodeProgramme.code == "354")).scalar_one_or_none()

    assert programme.id is not None
    assert programme.code == "354"

    assert ae.id is not None
    assert ae.source_region == "53"
    assert ae.annee == 2024
    assert ae.programme == "354"
    assert ae.n_poste_ej == 1
    assert ae.centre_couts == "ADCSDAT075"
    assert ae.referentiel_programmation == "035401010301"
    assert len(ae.montant_ae) == 1
    assert ae.montant_ae[0].montant == 9159575.18
    assert ae.montant_ae[0].annee == 2024
    assert ae.tranche_fonctionnelle is None
    assert ae.fonds is None
    assert ae.domaine_fonctionnel == "0354-02"
    assert ae.projet_analytique is None
    assert ae.axe_ministeriel_1 is None
    assert ae.axe_ministeriel_2 is None
    assert ae.societe == "BRET"
    assert ae.centre_financier == "0354-CDMA-CDAT"

    delete_references(session)
