from datetime import date
from unittest.mock import patch, call, ANY, MagicMock

from models.entities.financial.Ademe import Ademe
from models.entities.refs.Siret import Siret
from app.tasks.financial.import_financial import import_line_ademe, import_file_ademe
from tests import TESTS_PATH
from tests import delete_references

_ademe = TESTS_PATH / "data" / "ademe"


@patch("app.tasks.financial.import_financial.subtask")
def test_import_file_ademe(mock_subtask: MagicMock):
    # DO
    with patch("shutil.move", return_value=None):  # ne pas supprimer le fichier de tests :)
        import_file_ademe(_ademe / "ademe.csv")

    mock_subtask.assert_has_calls(
        [
            call().delay(
                '{"Nom de l attribuant":"ADEME","idAttribuant":"38529030900454","dateConvention":"2021-05-05","referenceDecision":"21BRD0090","nomBeneficiaire":"MEGO ! - MEGO","idBeneficiaire":"82815371800014","objet":"TREMPLIN pour la transition \\u00e9cologique des PME","montant":5000,"nature":"aide en num\\u00e9raire","conditionsVersement":"Echelonn\\u00e9","datesPeriodeVersement":"2021-05-11_2023-01-05","idRAE":null,"notificationUE":"NON","pourcentageSubvention":1.0}',
                ANY,
            ),
            call("import_line_ademe"),
        ],
        any_order=True,
    )


def test_import_line_ademe(app, database, session):
    # GIVEN
    data = '{"Nom de l attribuant":"ADEME","idAttribuant":"38529030900454","dateConvention":"2021-05-05","referenceDecision":"21BRD0090","nomBeneficiaire":"MEGO ! - MEGO","idBeneficiaire":82815371800014,"objet":"TREMPLIN pour la transition \u00e9cologique des PME","montant":400.1,"nature":"aide en num\u00e9raire","conditionsVersement":"Echelonn\u00e9","datesPeriodeVersement":"2021-05-11_2023-01-05","idRAE":null,"notificationUE":"NON","pourcentageSubvention":1}'
    siret = Siret(**{"code": "82815371800014"})
    session.add(siret)
    session.commit()
    # DO
    with patch(
        "app.services.siret.update_siret_from_api_entreprise",
        return_value=Siret(**{"code": "38529030900454", "code_commune": "35099"}),
    ):
        import_line_ademe(data, tech_info_list=("a task id", 1))

    # ASSERT
    data = session.execute(database.select(Ademe).where(Ademe.reference_decision == "21BRD0090")).scalar_one_or_none()
    assert data.id is not None
    assert data.montant == 400.1
    assert data.notification_ue is True
    assert data.date_convention == date(2021, 5, 5)
    assert data.siret_beneficiaire == "82815371800014"
    assert data.siret_attribuant == "38529030900454"
    assert data.dates_periode_versement == "2021-05-11_2023-01-05"
    delete_references(session)
