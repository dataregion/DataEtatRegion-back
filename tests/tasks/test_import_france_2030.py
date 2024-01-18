from unittest.mock import patch, MagicMock, call, ANY

from app.models.financial.France2030 import France2030
from app.models.refs.siret import Siret
from app.tasks.financial.import_france_2030 import import_file_france_2030, import_line_france_2030
from tests import TESTS_PATH

_data = TESTS_PATH / "data"


@patch("app.tasks.financial.import_france_2030.subtask")
def test_import_import_file(mock_subtask: MagicMock):
    # DO
    with patch("shutil.move", return_value=None):
        import_file_france_2030(_data / "france_2030" / "france_2030.csv", annee=2023)

    mock_subtask.assert_has_calls(
        [
            call().delay(
                '{"date_dpm":"2021-04-16","operateur":"BPI","procedure":"Contractualisation directe","nom_projet":"POLYCOR BIS","nom_beneficiaire":"CHU NANTES","siret":"26440013600471","typologie":"\\u00c9tablissements publics","regions":"Pays de la Loire","localisation_geo":44,"acteur_emergent":null,"nom_strategie":"Capacity building","code_nomenclature":"Objectif 7","nomenclature":"Produire en France au moins 20 bio-m\\u00e9dicaments, notamment contre les cancers, les maladies chroniques et d\\u00e9velopper et produire des dispositifs m\\u00e9dicaux innovants","montant_subvention":418492.0,"montant_avance_remboursable":null,"montant_aide":418492.0,"annee":2023}',
                ANY,
            ),
            call().delay(
                '{"date_dpm":"2021-04-16","operateur":"BPI","procedure":"Contractualisation directe","nom_projet":"EXT_XT","nom_beneficiaire":"LFB BIOMANUFACTURING","siret":"49927250800015","typologie":"Petites et moyennes entreprises","regions":"Occitanie","localisation_geo":30,"acteur_emergent":null,"nom_strategie":"Capacity building","code_nomenclature":"Objectif 7","nomenclature":"Produire en France au moins 20 bio-m\\u00e9dicaments, notamment contre les cancers, les maladies chroniques et d\\u00e9velopper et produire des dispositifs m\\u00e9dicaux innovants","montant_subvention":null,"montant_avance_remboursable":3489768.0,"montant_aide":3489768.0,"annee":2023}',
                ANY,
            ),
            call("import_line_france_2030"),
        ],
        any_order=True,
    )


def test_import_ligne_france_2030(database, session):
    # GIVEN
    data = '{"date_dpm":1631318400000,"operateur":"BPI","procedure":"Contractualisation directe","nom_projet":"RONSARD 2","nom_beneficiaire":"RECIPHARM MONTS","siret":"39922695000026","typologie":"Petites et moyennes entreprises","regions":"CVL","localisation_geo":37,"acteur_emergent":null,"nom_strategie":"Capacity building","code_nomenclature":"Objectif 7","nomemclature":"Produire en France au moins 20 bio-m\\u00e9dicaments, notamment contre les cancers, les maladies chroniques et d\\u00e9velopper et produire des dispositifs m\\u00e9dicaux innovants","montant_subvention":null,"montant_avance_remboursable":23372935.0,"montant_aide":23372935.0,"annee":2023}'
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
