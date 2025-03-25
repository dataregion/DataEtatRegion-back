import base64
import json
import pytest
import os


def pytest_addoption(parser):
    """Ajoute des options CLI à pytest"""
    parser.addoption(
        "--api-url", action="store", default=None, help="URL de l'API backend"
    )


@pytest.fixture(scope="session")
def api_base_url(pytestconfig):
    """Récupère l'URL de l'API depuis CLI, ENV ou config.yaml"""
    return pytestconfig.getoption("api_url") or os.getenv(
        "API_BASE_URL", "http://localhost:5000"
    )


@pytest.fixture(scope="session")
def fake_token():
    header = {"alg": "HS256", "typ": "JWT", "kid": "fake-key-id"}
    encoded_header = (
        base64.urlsafe_b64encode(json.dumps(header).encode()).decode().strip("=")
    )

    # Payload factice
    payload = {"user_id": 123, "role": "user"}
    encoded_payload = (
        base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().strip("=")
    )

    # Signature invalide (chaîne bidon)
    fake_signature = "invalidsignature"

    # Fake JWT final
    fake_jwt = f"{encoded_header}.{encoded_payload}.{fake_signature}"
    return fake_jwt
