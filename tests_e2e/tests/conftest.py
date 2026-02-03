import requests
import base64
import json
import pytest
import os


def pytest_addoption(parser):
    """Ajoute des options CLI à pytest"""
    parser.addoption("--api-url", action="store", default=None, help="URL de l'API backend")

    #############################
    #
    parser.addoption(
        "--keycloak-url",
        action="store",
        default=None,
        help="URL du keycloak",
    )

    parser.addoption(
        "--keycloak-realm",
        action="store",
        default=None,
        help="realm du keycloak",
    )

    parser.addoption(
        "--client-id",
        action="store",
        default=None,
        help="ID du client keycloak",
    )
    parser.addoption(
        "--client-id-with-no-rights",
        action="store",
        default=None,
        help="ID du client keycloak sans droits associé à l'utilisateur",
    )
    parser.addoption(
        "--client-secret",
        action="store",
        default=None,
        help="secret du client keycloak (si nécessaire)",
    )

    parser.addoption(
        "--username",
        action="store",
        default=None,
        help="Username du compte",
    )
    parser.addoption(
        "--password",
        action="store",
        default=None,
        help="Password du compte",
    )


##
@pytest.fixture(scope="session")
def keycloak_url(pytestconfig):
    """URL du keycloak"""
    return pytestconfig.getoption("keycloak_url") or os.getenv("KEYCLOAK_URL", "http://localhost:8080")


@pytest.fixture(scope="session")
def keycloak_realm(pytestconfig):
    """Realm du keycloak"""
    return pytestconfig.getoption("keycloak_realm") or os.getenv("KEYCLOAK_REALM", "test_realm")


@pytest.fixture(scope="session")
def client_id(pytestconfig):
    """client id de l'authent keycloak"""
    return pytestconfig.getoption("client_id") or os.getenv("CLIENT_ID", "test_client_id")


@pytest.fixture(scope="session")
def client_id_with_no_rights(pytestconfig):
    """client id de l'authent keycloak"""
    return pytestconfig.getoption("client_id_with_no_rights") or os.getenv(
        "CLIENT_ID_WITH_NO_RIGHTS", "test_client_id_with_no_rights"
    )


@pytest.fixture(scope="session")
def client_secret(pytestconfig):
    """client secret de l'authent keycloak"""
    return pytestconfig.getoption("client_secret") or os.getenv("CLIENT_SECRET", "test_client_secret")


@pytest.fixture(scope="session")
def username(pytestconfig):
    """username"""
    return pytestconfig.getoption("username") or os.getenv("USERNAME", "test_username")


@pytest.fixture(scope="session")
def password(pytestconfig):
    """password"""
    return pytestconfig.getoption("password") or os.getenv("PASSWORD", "test_password")


@pytest.fixture(scope="session")
def api_base_url(pytestconfig):
    """Récupère l'URL de l'API depuis CLI, ENV ou config.yaml"""
    return pytestconfig.getoption("api_url") or os.getenv("API_BASE_URL", "http://localhost:5000")


##


@pytest.fixture(scope="session")
def fake_token():
    header = {"alg": "HS256", "typ": "JWT", "kid": "fake-key-id"}
    encoded_header = base64.urlsafe_b64encode(json.dumps(header).encode()).decode().strip("=")

    # Payload factice
    payload = {"user_id": 123, "role": "user"}
    encoded_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().strip("=")

    # Signature invalide (chaîne bidon)
    fake_signature = "invalidsignature"

    # Fake JWT final
    fake_jwt = f"{encoded_header}.{encoded_payload}.{fake_signature}"
    return fake_jwt


@pytest.fixture(scope="session")
def real_token(keycloak_url, keycloak_realm, client_id, client_secret, username, password):
    return _real_token(keycloak_url, keycloak_realm, client_id, client_secret, username, password)


@pytest.fixture(scope="session")
def real_token_no_rights(keycloak_url, keycloak_realm, client_id_with_no_rights, client_secret, username, password):
    return _real_token(keycloak_url, keycloak_realm, client_id_with_no_rights, client_secret, username, password)


@pytest.fixture(scope="session")
def real_token_tampered(keycloak_url, keycloak_realm, client_id_with_no_rights, client_secret, username, password):
    """Représente un token réel qui a été altéré après sa création"""
    real_token = _real_token(keycloak_url, keycloak_realm, client_id_with_no_rights, client_secret, username, password)
    # Décoder le token JWT
    parts = real_token.split(".")
    if len(parts) != 3:
        raise ValueError("Token JWT invalide")

    # Décoder le payload (ajouter le padding si nécessaire)
    payload_b64 = parts[1]
    padding = 4 - len(payload_b64) % 4
    if padding != 4:
        payload_b64 += "=" * padding

    payload = json.loads(base64.urlsafe_b64decode(payload_b64))

    # Altérer les rôles
    if "realm_access" not in payload:
        payload["realm_access"] = {}
    if "roles" not in payload["realm_access"]:
        payload["realm_access"]["roles"] = []

    payload["realm_access"]["roles"].append("tampered_role")

    # Réencoder le payload
    tampered_payload = base64.urlsafe_b64encode(json.dumps(payload).encode()).decode().strip("=")

    # Reconstruire le token avec le payload altéré (signature invalide)
    tampered_token = f"{parts[0]}.{tampered_payload}.{parts[2]}"

    return tampered_token


@pytest.fixture(scope="session")
def real_token_with_client(keycloak_url, keycloak_realm, username, password):
    def connect_on_client(client_id, client_secret):
        return _real_token(keycloak_url, keycloak_realm, client_id, client_secret, username, password)

    return connect_on_client


def _real_token(keycloak_url, keycloak_realm, client_id, client_secret, username, password):
    """A and valid jwt token of connected user"""

    token_url = f"{keycloak_url}/realms/{keycloak_realm}/protocol/openid-connect/token"

    data = {
        "grant_type": "password",
        "client_id": client_id,
        "username": username,
        "password": password,
    }
    if client_secret is not None:
        data["client_secret"] = client_secret

    response = requests.post(token_url, data=data)

    if response.status_code == 200:
        token = response.json()["access_token"]
    else:
        raise RuntimeError("Impossible de récupérer un token réel")
    return token
