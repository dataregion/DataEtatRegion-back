from . import apis_externes_v3  # type: ignore # noqa: F401
from tests_e2e.utils import call_request

####################################################
#

def test_api_entreprise_v3_nonconnecte(apis_externes_v3):  # noqa: F811
    siret = "26350579400028"
    response = call_request(f"{apis_externes_v3}/info-entreprise/{siret}")

    assert response.status_code == 401

def test_api_entreprise_v3_with_bad_token(apis_externes_v3, fake_token):  # noqa: F811
    siret = "26350579400028"
    response = call_request(f"{apis_externes_v3}/info-entreprise/{siret}", token=fake_token)
    assert response.status_code == 401

####################################################
#
def test_api_entreprise_v3(apis_externes_v3, real_token):  # noqa: F811
    siret = "26350579400028"
    response = call_request(f"{apis_externes_v3}/info-entreprise/{siret}", token=real_token)

    assert response.status_code == 200
    response_json = response.json()
    assert len(response_json.keys()) > 5
    assert 'donnees_etablissement' in response_json

def test_api_entreprise_v3_siret_inexistant(apis_externes_v3, real_token):  # noqa: F811
    siret_inexistant = "30613890000131"

    response = call_request(f"{apis_externes_v3}/info-entreprise/{siret_inexistant}", token=real_token)
    
    assert response.status_code == 500
    response_json = response.json()
    assert 'REMOTE_CALL_FAILED' == response_json['code']