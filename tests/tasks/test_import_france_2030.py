from unittest.mock import patch, MagicMock, call, ANY

from app.models.financial.France2030 import France2030
from app.models.refs.siret import Siret
from app.tasks.financial.import_france_2030 import import_file_france_2030, import_line_france_2030
from tests import DATA_PATH

_data = DATA_PATH / "data"


@patch("app.tasks.financial.import_france_2030.subtask")
def test_import_import_file(mock_subtask: MagicMock):
    # DO
    with patch("shutil.move", return_value=None):
        import_file_france_2030(_data / "france_2030" / "france_2030.xlsx")

    mock_subtask.assert_has_calls(
        [
            call().delay(
                '{"date_dpm":1629849600000,"operateur":"ANR","procedure":"D\\u00e9monstrateurs num\\u00e9riques dans l\'enseignement sup\\u00e9rieur (DemoES)","nom_projet":"PEIA","nom_beneficiaire":"Universit\\u00e9 Polytechnique Hauts-de-France","siret":"19593279300019","typologie":"\\u00c9tablissements publics","regions":"Hauts-de-France","localisation_geo":59,"acteur_emergent":null,"nom_strategie":"SA Enseignement et num\\u00e9rique","code_nomenclature":"Levier 3","nomemclature":"D\\u00e9velopper les talents\\u00a0en construisant les formations de demain\\u00a0","montant_subvention":5000000.0,"montant_avance_remboursable":null,"montant_aide":5000000.0}',
                ANY,
            ),
            call().delay(
                '{"date_dpm":1631318400000,"operateur":"BPI","procedure":"Contractualisation directe","nom_projet":"RONSARD 2","nom_beneficiaire":"RECIPHARM MONTS","siret":"39922695000026","typologie":"Petites et moyennes entreprises","regions":"CVL","localisation_geo":37,"acteur_emergent":null,"nom_strategie":"Capacity building","code_nomenclature":"Objectif 7","nomemclature":"Produire en France au moins 20 bio-m\\u00e9dicaments, notamment contre les cancers, les maladies chroniques et d\\u00e9velopper et produire des dispositifs m\\u00e9dicaux innovants","montant_subvention":null,"montant_avance_remboursable":23372935.0,"montant_aide":23372935.0}',
                ANY,
            ),
            call("import_line_france_2030"),
        ],
        any_order=True,
    )


def test_import_ligne_france_2030(database, session):
    # GIVEN
    data = '{"date_dpm":1631318400000,"operateur":"BPI","procedure":"Contractualisation directe","nom_projet":"RONSARD 2","nom_beneficiaire":"RECIPHARM MONTS","siret":"39922695000026","typologie":"Petites et moyennes entreprises","regions":"CVL","localisation_geo":37,"acteur_emergent":null,"nom_strategie":"Capacity building","code_nomenclature":"Objectif 7","nomemclature":"Produire en France au moins 20 bio-m\\u00e9dicaments, notamment contre les cancers, les maladies chroniques et d\\u00e9velopper et produire des dispositifs m\\u00e9dicaux innovants","montant_subvention":null,"montant_avance_remboursable":23372935.0,"montant_aide":23372935.0}'
    # DO

    with patch(
        "app.services.siret.update_siret_from_api_entreprise",
        return_value=Siret(**{"code": "39922695000026", "code_commune": "35099"}),
    ):
        import_line_france_2030(data, tech_info_list=("a task id", 1))

    # ASSERT
    data: France2030 = session.execute(
        database.select(France2030).filter_by(siret="39922695000026")
    ).scalar_one_or_none()
    assert data.id is not None
    assert data.nom_projet == "RONSARD 2"
    assert data.siret == "39922695000026"
    assert data.code_nomenclature == "Objectif 7"
