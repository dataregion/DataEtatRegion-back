from . import apis_externes_v3  # type: ignore # noqa: F401
from tests_e2e.utils import call_request
####################################################
#


def test_api_subventions_v3_nonconnecte(apis_externes_v3):  # noqa: F811
    siret = "26350579400028"
    response = call_request(f"{apis_externes_v3}/info-subvention/{siret}")

    assert response.status_code == 401


def test_api_subventions_v3_with_bad_token(apis_externes_v3, fake_token):  # noqa: F811
    siret = "26350579400028"
    response = call_request(f"{apis_externes_v3}/info-subvention/{siret}", token=fake_token)
    assert response.status_code == 401


####################################################
#
def test_api_subventions_v3(apis_externes_v3, real_token):  # noqa: F811
    siret = "77774350100044"
    response = call_request(f"{apis_externes_v3}/info-subvention/{siret}", token=real_token)

    assert response.status_code == 200
    assert "subventions" in response.json()


def test_api_subventions_v3_notanassociation(apis_externes_v3, real_token):  # noqa: F811
    siret = "54210780003943"
    response = call_request(f"{apis_externes_v3}/info-subvention/{siret}", token=real_token)

    assert response.status_code == 500
    response_json = response.json()
    assert 0 == response_json["remote_errors"][0]["api_code"]
    assert "message" in response_json["remote_errors"][0]


def test_api_subventions_v3_siret_inexistant(apis_externes_v3, real_token):  # noqa: F811
    siret_inexistant = "77774350100043"

    response = call_request(f"{apis_externes_v3}/info-subvention/{siret_inexistant}", token=real_token)

    assert response.status_code == 500
    response_json = response.json()
    assert "REMOTE_CALL_FAILED" == response_json["code"]
    assert 404 == response_json["remote_errors"][0]["status_code"]
