"""Tests pour le routeur de gestion des préférences utilisateur.

Ce module teste tous les endpoints du routeur preferences :
- POST /users/preferences : Création de préférences
- GET /users/preferences : Liste des préférences
- GET /users/preferences/{uuid} : Récupération d'une préférence
- POST /users/preferences/{uuid} : Mise à jour d'une préférence
- DELETE /users/preferences/{uuid} : Suppression d'une préférence
"""

import pytest
from http import HTTPStatus
from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from models.entities.preferences.Preference import Preference, Share

from apis.clients.keycloak_admin import KeycloakAdminError

from .conftest import *  # noqa: F401, F403

from prefect.client.schemas.objects import FlowRun

# Préfixe de l'API administration
API_PREFIX = "/administration/api/v3"


# ============================================================================
# TESTS DE CRÉATION (POST /users/preferences)
# ============================================================================


def test_create_preference_without_shares(
    client: TestClient,
    session_settings: Session,
    mock_connected_user,
):
    """Test de création d'une préférence sans partage.

    Vérifie que :
    - La préférence est créée avec succès (status 201)
    - Les données retournées sont correctes
    - Prefect n'est PAS appelé (pas de partage)
    - La préférence existe bien en base de données
    """
    # Préparer les données
    payload = {
        "name": "Ma nouvelle préférence",
        "filters": {"annee": 2024, "type": "test"},
        "options": {"display": "grid"},
        "shares": [],
    }

    # Appeler l'endpoint
    response = client.post(f"{API_PREFIX}/users/preferences", json=payload)

    # Vérifications
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert data["code"] == HTTPStatus.CREATED
    assert data["message"] == "Préférence créée avec succès"
    assert data["data"]["name"] == payload["name"]
    assert data["data"]["filters"] == payload["filters"]
    assert data["data"]["options"] == payload["options"]
    assert data["data"]["username"] == mock_connected_user.email
    assert "uuid" in data["data"]
    assert isinstance(data["data"]["shares"], list)
    assert len(data["data"]["shares"]) == 0

    # Vérifier en base de données
    pref_uuid = data["data"]["uuid"]
    pref = session_settings.query(Preference).filter_by(uuid=pref_uuid).first()
    assert pref is not None
    assert pref.name == payload["name"]
    assert pref.username == mock_connected_user.email

    # Cleanup
    session_settings.delete(pref)
    session_settings.commit()


@patch("apis.apps.administration.routers.preferences.get_origin_referrer")
@patch("apis.apps.administration.routers.preferences.arun_deployment")
def test_create_preference_with_shares(
    mock_run_deployment,
    mock_get_origin,
    client: TestClient,
    session_settings: Session,
    mock_connected_user,
):
    """Test de création d'une préférence avec partage.

    Vérifie que :
    - La préférence est créée avec le partage
    - Prefect EST appelé avec les bons paramètres
    - Le Share existe en base de données
    """
    # Mock de l'origin pour le lien de partage
    mock_get_origin.return_value = "http://localhost:4200"
    mock_run_deployment.return_value = FlowRun(
        id="550e8400-e29b-41d4-a716-446655440000", flow_id="550e8400-e29b-41d4-a716-446655440000"
    )

    # Préparer les données
    payload = {
        "name": "Préférence partagée",
        "filters": {"region": "Bretagne"},
        "options": {},
        "shares": [
            {"shared_username_email": "user1@example.com"},
            {"shared_username_email": "user2@example.com"},
        ],
    }

    # Appeler l'endpoint
    response = client.post(f"{API_PREFIX}/users/preferences", json=payload)

    # Vérifications
    assert response.status_code == HTTPStatus.CREATED
    data = response.json()
    assert len(data["data"]["shares"]) == 2

    # Vérifier l'appel à Prefect
    mock_run_deployment.assert_called_once()
    call_args = mock_run_deployment.call_args
    assert call_args[1]["name"] == "share-filter-user/share_filter_user"
    assert "preference_uuid" in call_args[1]["parameters"]
    assert call_args[1]["parameters"]["host_link"] == "http://localhost:4200"
    assert call_args[1]["timeout"] == 0  # fire and forget

    # Vérifier en base de données
    pref_uuid = data["data"]["uuid"]
    pref = session_settings.query(Preference).filter_by(uuid=pref_uuid).first()
    assert pref is not None
    assert len(pref.shares) == 2

    share_emails = [s.shared_username_email for s in pref.shares]
    assert "user1@example.com" in share_emails
    assert "user2@example.com" in share_emails

    # Cleanup
    session_settings.delete(pref)
    session_settings.commit()


@patch("apis.apps.administration.routers.preferences.arun_deployment")
def test_create_preference_prefect_error_does_fail(
    mock_run_deployment,
    client: TestClient,
    session_settings: Session,
):
    """Test que l'erreur Prefect n'empêche pas la création.

    Si l'envoi d'email échoue, la préférence doit quand même être créée.
    """
    # Simuler une erreur Prefect
    mock_run_deployment.side_effect = Exception("Prefect unavailable")

    payload = {
        "name": "Test erreur Prefect",
        "filters": {},
        "options": {},
        "shares": [{"shared_username_email": "other@example.com"}],
    }

    # L'endpoint doit réussir malgré l'erreur Prefect
    response = client.post(f"{API_PREFIX}/users/preferences", json=payload)

    with pytest.raises(Exception):
        response.raise_for_status()

    # Vérifie que la préférence n'a pas été créée malgré l'erreur Prefect
    pref = session_settings.query(Preference).all()
    assert len(pref) == 0, "L'échec de Prefect n'a pas empêché la création de la préférence"


# ============================================================================
# TESTS DE LISTE ET RÉCUPÉRATION (GET /users/preferences)
# ============================================================================


def test_list_preferences(
    client: TestClient,
    shared_preference: Preference,
    unshared_preference: Preference,
):
    """Test de récupération de la liste des préférences.

    Vérifie que :
    - Les préférences créées par l'utilisateur sont dans create_by_user
    - Les préférences partagées avec l'utilisateur sont dans shared_with_user
    """
    # Appeler l'endpoint
    response = client.get(f"{API_PREFIX}/users/preferences")

    # Vérifications
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["code"] == HTTPStatus.OK
    assert "create_by_user" in data["data"]
    assert "shared_with_user" in data["data"]

    # L'utilisateur a créé 2 préférences
    created = data["data"]["create_by_user"]
    assert len(created) == 2

    # Vérifier que nos fixtures sont présentes
    created_uuids = [p["uuid"] for p in created]
    assert shared_preference.uuid in created_uuids
    assert unshared_preference.uuid in created_uuids

    # Pour l'instant, aucune préférence partagée AVEC lui
    shared = data["data"]["shared_with_user"]
    assert len(shared) == 0


def test_list_preferences_with_shared(
    client: TestClient,
    shared_preference: Preference,
    preference_shared_with_user: Preference,
):
    """Test avec une préférence partagée AVEC l'utilisateur."""
    response = client.get(f"{API_PREFIX}/users/preferences")

    assert response.status_code == HTTPStatus.OK
    data = response.json()

    # Au moins 1 créée par l'utilisateur
    created = data["data"]["create_by_user"]
    assert len(created) >= 1

    # 1 partagée avec l'utilisateur
    shared = data["data"]["shared_with_user"]
    assert len(shared) == 1
    assert shared[0]["uuid"] == preference_shared_with_user.uuid
    assert shared[0]["username"] == "shareowner"


def test_get_preference_by_uuid(
    client: TestClient,
    session_settings: Session,
    shared_preference: Preference,
):
    """Test de récupération d'une préférence par UUID.

    Vérifie que :
    - La préférence est récupérée correctement
    - Le compteur d'utilisation est incrémenté
    """
    # Sauvegarder le compteur initial
    initial_count = shared_preference.nombre_utilisation

    # Appeler l'endpoint
    response = client.get(f"{API_PREFIX}/users/preferences/{shared_preference.uuid}")

    # Vérifications
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["code"] == HTTPStatus.OK
    assert data["data"]["uuid"] == shared_preference.uuid
    assert data["data"]["name"] == shared_preference.name
    assert data["data"]["filters"] == shared_preference.filters

    # Vérifier l'incrémentation du compteur
    session_settings.refresh(shared_preference)
    assert shared_preference.nombre_utilisation == initial_count + 1


def test_get_preference_not_found(client: TestClient):
    """Test de récupération d'une préférence inexistante."""
    fake_uuid = "fake-uuid-12345"

    response = client.get(f"{API_PREFIX}/users/preferences/{fake_uuid}")

    assert response.status_code == HTTPStatus.BAD_REQUEST
    data = response.json()
    assert "introuvable" in data["message"].lower()


# ============================================================================
# TESTS DE MISE À JOUR (POST /users/preferences/{uuid})
# ============================================================================


@patch("apis.apps.administration.routers.preferences.arun_deployment")
def test_update_preference_without_shares(
    mock_run_deployment,
    client: TestClient,
    session_settings: Session,
    unshared_preference: Preference,
):
    """Test de mise à jour d'une préférence sans partage.

    Vérifie que :
    - Les données sont mises à jour correctement
    - Prefect n'est PAS appelé
    """
    # Préparer les nouvelles données
    payload = {
        "name": "Nom modifié",
        "filters": {"annee": 2026, "updated": True},
        "options": {"new_option": "value"},
        "shares": [],
    }

    # Appeler l'endpoint
    response = client.post(
        f"{API_PREFIX}/users/preferences/{unshared_preference.uuid}",
        json=payload,
    )

    # Vérifications
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["code"] == HTTPStatus.OK
    assert data["message"] == "Préférence mise à jour avec succès"

    # Vérifier que Prefect n'est PAS appelé
    mock_run_deployment.assert_not_called()

    # Vérifier en base de données
    session_settings.refresh(unshared_preference)
    assert unshared_preference.name == "Nom modifié"
    assert unshared_preference.filters == {"annee": 2026, "updated": True}
    assert unshared_preference.options == {"new_option": "value"}


@patch("apis.apps.administration.routers.preferences.get_origin_referrer")
@patch("apis.apps.administration.routers.preferences.arun_deployment")
def test_update_preference_with_shares(
    mock_run_deployment,
    mock_get_origin,
    client: TestClient,
    session_settings: Session,
    unshared_preference: Preference,
):
    """Test de mise à jour avec ajout de partages.

    Vérifie que :
    - Les partages sont ajoutés
    - Prefect EST appelé
    """
    mock_get_origin.return_value = "http://localhost:4200"
    mock_run_deployment.return_value = FlowRun(
        id="550e8400-e29b-41d4-a716-446655440000", flow_id="550e8400-e29b-41d4-a716-446655440000"
    )

    payload = {
        "name": unshared_preference.name,
        "filters": unshared_preference.filters,
        "options": unshared_preference.options,
        "shares": [
            {"shared_username_email": "newshare@example.com"},
        ],
    }

    # Appeler l'endpoint
    response = client.post(
        f"{API_PREFIX}/users/preferences/{unshared_preference.uuid}",
        json=payload,
    )

    # Vérifications
    assert response.status_code == HTTPStatus.OK

    # Vérifier l'appel à Prefect
    mock_run_deployment.assert_called_once()

    # Vérifier en base de données
    session_settings.refresh(unshared_preference)
    assert len(unshared_preference.shares) == 1
    assert unshared_preference.shares[0].shared_username_email == "newshare@example.com"


@patch("apis.apps.administration.routers.preferences.arun_deployment")
def test_update_preference_prefect_error_does_fail(
    mock_run_deployment,
    client: TestClient,
    session_settings: Session,
    unshared_preference: Preference,
):
    """Test que l'erreur Prefect empêche la mise à jour.

    Si l'envoi d'email échoue, la préférence ne doit pas être mise à jour.
    """
    # Sauvegarder l'état initial de la préférence
    initial_name = unshared_preference.name
    initial_filters = unshared_preference.filters.copy()
    initial_options = unshared_preference.options.copy()
    initial_shares_count = len(unshared_preference.shares)

    # Simuler une erreur Prefect
    mock_run_deployment.side_effect = Exception("Prefect unavailable")

    payload = {
        "name": "Nom modifié avec erreur",
        "filters": {"annee": 2027, "error_test": True},
        "options": {"error_option": "value"},
        "shares": [{"shared_username_email": "errortest@example.com"}],
    }

    # L'endpoint doit échouer à cause de l'erreur Prefect
    response = client.post(
        f"{API_PREFIX}/users/preferences/{unshared_preference.uuid}",
        json=payload,
    )

    with pytest.raises(Exception):
        response.raise_for_status()

    # Vérifier que la préférence n'a PAS été mise à jour
    session_settings.refresh(unshared_preference)
    assert unshared_preference.name == initial_name
    assert unshared_preference.filters == initial_filters
    assert unshared_preference.options == initial_options
    assert len(unshared_preference.shares) == initial_shares_count


def test_update_preference_forbidden(
    client: TestClient,
    other_user_preference: Preference,
):
    """Test de mise à jour d'une préférence d'un autre utilisateur.

    Doit retourner une erreur 403 Forbidden.
    """
    payload = {
        "name": "Tentative de modification",
        "filters": {},
        "options": {},
        "shares": [],
    }

    response = client.post(
        f"{API_PREFIX}/users/preferences/{other_user_preference.uuid}",
        json=payload,
    )

    # Doit être interdit
    assert response.status_code == HTTPStatus.FORBIDDEN


def test_update_preference_not_found(client: TestClient):
    """Test de mise à jour d'une préférence inexistante."""
    payload = {
        "name": "Test",
        "filters": {},
        "options": {},
        "shares": [],
    }

    response = client.post(f"{API_PREFIX}/users/preferences/fake-uuid", json=payload)

    assert response.status_code == HTTPStatus.BAD_REQUEST


# ============================================================================
# TESTS DE SUPPRESSION (DELETE /users/preferences/{uuid})
# ============================================================================


def test_delete_preference(
    client: TestClient,
    session_settings: Session,
    shared_preference: Preference,
):
    """Test de suppression d'une préférence.

    Vérifie que :
    - La préférence est supprimée
    - Les partages sont supprimés en cascade
    """
    pref_uuid = shared_preference.uuid
    pref_id = shared_preference.id

    # Vérifier qu'il y a des partages
    shares_count = len(shared_preference.shares)
    assert shares_count > 0

    # Appeler l'endpoint
    response = client.delete(f"{API_PREFIX}/users/preferences/{pref_uuid}")

    # Vérifications
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["code"] == HTTPStatus.OK
    assert data["message"] == "Préférence supprimée avec succès"

    # Vérifier que la préférence n'existe plus
    pref = session_settings.query(Preference).filter_by(uuid=pref_uuid).first()
    assert pref is None

    # Vérifier que les partages sont supprimés (cascade)
    shares = session_settings.query(Share).filter_by(preference_id=pref_id).all()
    assert len(shares) == 0


def test_delete_preference_forbidden(
    client: TestClient,
    session_settings: Session,
    other_user_preference: Preference,
):
    """Test de suppression d'une préférence d'un autre utilisateur.

    Doit retourner une erreur 403 Forbidden.
    """
    response = client.delete(f"{API_PREFIX}/users/preferences/{other_user_preference.uuid}")

    # Doit être interdit
    assert response.status_code == HTTPStatus.FORBIDDEN

    # Vérifier que la préférence existe toujours
    pref = session_settings.query(Preference).filter_by(uuid=other_user_preference.uuid).first()
    assert pref is not None


def test_delete_preference_not_found(client: TestClient):
    """Test de suppression d'une préférence inexistante."""
    response = client.delete(f"{API_PREFIX}/users/preferences/fake-uuid")

    assert response.status_code == HTTPStatus.BAD_REQUEST


# ============================================================================
# TESTS DE RECHERCHE D'UTILISATEURS (GET /users/preferences/search-user)
# ============================================================================


@patch("apis.apps.administration.routers.preferences.get_keycloak_admin")
def test_search_users_success(mock_get_keycloak_admin, client: TestClient):
    """Test de recherche d'utilisateurs Keycloak avec succès.

    Vérifie que :
    - Les résultats de Keycloak sont retournés correctement
    - Le format de réponse est correct
    """
    # Mock du client Keycloak
    mock_admin = MagicMock()
    mock_admin.get_users.return_value = [
        {"username": "user1", "email": "user1@example.com"},
        {"username": "user2", "email": "user2@example.com"},
        {"username": "user123", "email": "user123@example.com"},
    ]
    mock_get_keycloak_admin.return_value = mock_admin

    # Appeler l'endpoint
    response = client.get(f"{API_PREFIX}/users/preferences/search-user?username=user")

    # Vérifications
    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert data["code"] == HTTPStatus.OK
    assert len(data["data"]) == 3
    assert data["data"][0]["username"] == "user1"
    assert data["data"][1]["username"] == "user2"
    assert data["data"][2]["username"] == "user123"

    # Vérifier l'appel à Keycloak
    mock_admin.get_users.assert_called_once()
    call_args = mock_admin.get_users.call_args[0][0]
    assert call_args["search"] == "user"
    assert call_args["enabled"] is True
    assert call_args["briefRepresentation"] is True


def test_search_users_too_short(client: TestClient):
    """Test de recherche avec un terme trop court.

    FastAPI devrait rejeter la requête car min_length=4.
    """
    response = client.get(f"{API_PREFIX}/users/preferences/search-user?username=ab")

    # Devrait être rejeté par la validation FastAPI
    assert response.status_code == HTTPStatus.UNPROCESSABLE_ENTITY


def test_search_users_minimum_length(client: TestClient):
    """Test avec exactement 4 caractères (minimum accepté)."""
    with patch("apis.apps.administration.routers.preferences.get_keycloak_admin") as mock_kc:
        mock_admin = MagicMock()
        mock_admin.get_users.return_value = [{"username": "test"}]
        mock_kc.return_value = mock_admin

        response = client.get(f"{API_PREFIX}/users/preferences/search-user?username=test")

        assert response.status_code == HTTPStatus.OK


@patch("apis.apps.administration.routers.preferences.get_keycloak_admin")
def test_search_users_keycloak_error(mock_get_keycloak_admin, client: TestClient):
    """Test avec une erreur Keycloak.

    Vérifie que l'erreur est correctement gérée et retournée.
    """
    # Simuler une erreur Keycloak
    mock_admin = MagicMock()
    mock_admin.get_users.side_effect = KeycloakAdminError("Connection error")
    mock_get_keycloak_admin.return_value = mock_admin

    # Appeler l'endpoint
    response = client.get(f"{API_PREFIX}/users/preferences/search-user?username=testuser")

    # Vérifications
    assert response.status_code == HTTPStatus.BAD_REQUEST
    data = response.json()
    assert "keycloak" in data["message"].lower()


@patch("apis.apps.administration.routers.preferences.get_keycloak_admin")
def test_search_users_empty_result(mock_get_keycloak_admin, client: TestClient):
    """Test avec aucun résultat trouvé."""
    mock_admin = MagicMock()
    mock_admin.get_users.return_value = []
    mock_get_keycloak_admin.return_value = mock_admin

    response = client.get(f"{API_PREFIX}/users/preferences/search-user?username=nonexistent")

    assert response.status_code == HTTPStatus.OK
    data = response.json()
    assert len(data["data"]) == 0
    assert "trouvé" in data["message"]
