from tests.controller.financial_data.utils_test_budget_v3 import (
    sanitize_region,
    unsafe_jwt_decode,
    lignes_first_id,  # noqa: F401
    assert_api_response_status,
)
from . import *  # noqa: F403
from tests_e2e.utils import call_request


#########
# Avec authentification KO
def test_budget_with_no_token(api_budget_v3):
    response = call_request(f"{api_budget_v3}/lignes", token=None)
    assert response.status_code == 401


def test_budget_with_bad_token(api_budget_v3, fake_token):
    response = call_request(f"{api_budget_v3}/lignes", token=fake_token)
    assert response.status_code == 401


#########
# Test lignes


def test_budget_lines_sort_on_id(api_budget_v3, real_token):
    """Les lignes sont, par défaut, triées par id ASC"""
    response = call_request(f"{api_budget_v3}/lignes", token=real_token)
    lignes = response.json()["data"]["lignes"]
    ids = [x["id"] for x in lignes]

    assert ids == sorted(ids), "Par défaut, on doit sort par id"


def test_budget_lines_sort_on_id_last(api_budget_v3, real_token):
    """Les lignes prennent en compte de tri et ajoutent by id ASC"""
    response = call_request(
        f"{api_budget_v3}/lignes?colonnes=beneficiaire_code&sort_by=beneficiaire_code&sort_order=asc",
        token=real_token,
    )
    lignes = response.json()["data"]["lignes"]
    sirets = [x["beneficiaire_code"] for x in lignes]

    for siret in sirets:
        ids_of_siret = [x["id"] for x in lignes if x["beneficiaire_code"] == siret]
        assert ids_of_siret == sorted(ids_of_siret)

    assert sirets == sorted(sirets), "Par défaut, on doit sort par id"


def test_budget_lignes_appartient_region_de_connexion_utilisateur(
    api_budget_v3,
    real_token,
):
    """
    La connexion de l'utilisateur porte potentiellement une région.
    Cette région applique un filtre sur ce que peut consulter l'utilisateur
    """

    token = unsafe_jwt_decode(real_token)
    connected_region = token["region"]
    response = call_request(
        f"{api_budget_v3}/lignes?colonnes=source_region",
        token=real_token,
    )
    lignes = response.json()["data"]["lignes"]
    regions_in_response = [x["source_region"] for x in lignes]
    regions_in_response = list(set(regions_in_response))

    assert len(regions_in_response) == 1 and sanitize_region(
        regions_in_response[0]
    ) == sanitize_region(connected_region)


def test_budget_lignes_source_region_pris_en_compte(
    api_budget_v3,
    real_token,
):
    token = unsafe_jwt_decode(real_token)
    connected_region = token["region"]
    assert connected_region != "999"
    response = call_request(
        f"{api_budget_v3}/lignes?colonnes=source_region&source_region=999",
        token=real_token,
    )
    assert_api_response_status(response, 204)


def test_budget_retourne_aggregation_sur_param_grouping(
    api_budget_v3,
    real_token,
):
    response = call_request(
        f"{api_budget_v3}/lignes?grouping=annee",
        token=real_token,
    )
    assert_api_response_status(response, 200)
    assert response.json()["data"]["type"] == "groupings"


def test_budget_retourne_lignes_sur_grouping_and_grouped(
    api_budget_v3,
    real_token,
):
    response = call_request(
        f"{api_budget_v3}/lignes?grouping=annee&grouped=2022",
        token=real_token,
    )
    assert_api_response_status(response, 200)
    assert response.json()["data"]["type"] == "lignes_financieres"


#########
# Test ligne
def test_budget_get_ligne_ok(api_budget_v3, real_token, lignes_first_id):  # noqa: F811
    response = call_request(
        f"{api_budget_v3}/lignes/{int(lignes_first_id)}?source=FINANCIAL_DATA_CP",
        token=real_token,
    )
    assert_api_response_status(response, 200)


def test_budget_get_ligne_not_found(api_budget_v3, real_token):  # noqa: F811
    response = call_request(
        f"{api_budget_v3}/lignes/0000000?source=FINANCIAL_DATA_AE",
        token=real_token,
    )
    assert_api_response_status(response, 404)


#########
# Test colonnes
def test_budget_get_lignes_check_param_grouping(api_budget_v3, real_token):  # noqa: F811
    response = call_request(
        f"{api_budget_v3}/lignes?grouping=id",
        token=real_token,
    )
    assert_api_response_status(response, 400)


def test_budget_get_lignes_check_param_colonnes(api_budget_v3, real_token):  # noqa: F811
    response = call_request(
        f"{api_budget_v3}/lignes?colonnes=source_region,type_pokemon",
        token=real_token,
    )
    assert_api_response_status(response, 400)


def test_budget_get_lignes_check_param_sort_by(api_budget_v3, real_token):  # noqa: F811
    response = call_request(
        f"{api_budget_v3}/lignes?sort_by=type_pokemon&sort_order=asc",
        token=real_token,
    )
    assert_api_response_status(response, 400)


def test_budget_get_lignes_check_param_fields_search(api_budget_v3, real_token):  # noqa: F811
    response = call_request(
        f"{api_budget_v3}/lignes?search=rennes&fields_search=pokemon",
        token=real_token,
    )
    assert_api_response_status(response, 400)


#########
# Test paires de paramètres
def test_budget_get_lignes_check_pairs(api_budget_v3, real_token):  # noqa: F811
    response = call_request(
        f"{api_budget_v3}/lignes?niveau_geo=Region",
        token=real_token,
    )
    assert_api_response_status(response, 400)
    response = call_request(
        f"{api_budget_v3}/lignes?code_geo=53",
        token=real_token,
    )
    assert_api_response_status(response, 400)

    response = call_request(
        f"{api_budget_v3}/lignes?sort_by=source_region",
        token=real_token,
    )
    assert_api_response_status(response, 400)
    response = call_request(
        f"{api_budget_v3}/lignes?sort_order=asc",
        token=real_token,
    )
    assert_api_response_status(response, 400)

    response = call_request(
        f"{api_budget_v3}/lignes?search=pokemon",
        token=real_token,
    )
    assert_api_response_status(response, 400)
    response = call_request(
        f"{api_budget_v3}/lignes?fields_search=source_region",
        token=real_token,
    )
    assert_api_response_status(response, 400)


#########
# Test paramètres grouping et grouped
def test_budget_get_lignes_check_grouping_and_grouped(api_budget_v3, real_token):  # noqa: F811
    response = call_request(
        f"{api_budget_v3}/lignes?grouping=programme_theme,beneficiaire_commune_code",
        token=real_token,
    )
    assert_api_response_status(response, 400)
    response = call_request(
        f"{api_budget_v3}/lignes?grouping=programme_theme,beneficiaire_commune_code&grouped=53,35650,22",
        token=real_token,
    )
    assert_api_response_status(response, 400)


def test_budget_get_lignes_avec_tags(api_budget_v3, real_token):  # noqa: F811
    response = call_request(
        f"{api_budget_v3}/lignes?tags=detr",
        token=real_token,
    )
    assert_api_response_status(response, 200)
    first_line_tags = response.json()["data"]["lignes"][0]["tags"]
    assert len(first_line_tags) > 0


# TODO: ici, continuer à qualifier l'api v3
