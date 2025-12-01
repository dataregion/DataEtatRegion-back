def test_keycloak_mock_is_active(mock_connected_user):
    """Vérifie que le mock Keycloak est bien actif."""
    from apis.security.keycloak_token_validator import KeycloakTokenValidator

    validator = KeycloakTokenValidator.get_application_instance()
    user = validator.validate_token("any-fake-token")

    assert user.email == "test@example.com"
    print("✓ Mock Keycloak fonctionne correctement")
