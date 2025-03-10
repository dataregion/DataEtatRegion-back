from unittest.mock import patch, MagicMock


@patch("app.servicesapp.authentication.connected_user.ConnectedUser.from_current_token_identity")
@patch("authlib.integrations.flask_oauth2.ResourceProtector")
def test_get_ressources(auth_mock, user_mock, test_client):
    mock_user = MagicMock()
    mock_user.current_region = "053"
    user_mock.return_value = mock_user
    auth_mock.token_auth.return_value = True

    response = test_client.get("ressource/liste")
    assert response.status_code == 200

    expected_data = {
        "visuterritoire": "https://geobretagne.fr/mviewer/?config=/apps/visuterritoire/config.xml",
        "graphiques": "http://localhost:8088/",
        "api_swagger": "http://localhost:5000/budget/api/v1",
        "documentation": "https://github.com/dataregion/DataEtatRegion-docs/blob/main/budget/DataEtatBretagne_Notice-utilisation-Budget_032023.pdf",
        "suivi_usage": "",
        "grist": "https://grist.nocode.csm.ovh/o/docs/login?next=%2F",
    }
    assert response.get_json() == expected_data


@patch("app.servicesapp.authentication.connected_user.ConnectedUser.from_current_token_identity")
@patch("authlib.integrations.flask_oauth2.ResourceProtector")
def test_get_default_ressources(auth_mock, user_mock, test_client):
    mock_user = MagicMock()
    mock_user.current_region = "999"
    user_mock.return_value = mock_user
    auth_mock.token_auth.return_value = True

    response = test_client.get("ressource/liste")
    assert response.status_code == 200

    expected_data = {
        "graphiques": "http://localhost:8088/",
        "api_swagger": "http://localhost:5000/budget/api/v1",
        "documentation": "https://github.com/dataregion/DataEtatRegion-docs/blob/main/budget/DataEtatBretagne_Notice-utilisation-Budget_032023.pdf",
        "suivi_usage": "",
        "grist": "https://grist.nocode.csm.ovh/o/docs/login?next=%2F",
    }
    assert response.get_json() == expected_data
