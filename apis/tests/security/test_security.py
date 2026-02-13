import pytest


@pytest.mark.asyncio
async def test_keycloak_mock_is_active(patch_keycloak_validator):
    """Vérifie que le mock Keycloak est bien actif."""
    from apis.security.keycloak_token_validator import KeycloakTokenValidator

    validator = KeycloakTokenValidator.get_application_instance()
    user = await validator.validate_token("any-fake-token")

    assert user.email == "test@example.com"
    print("✓ Mock Keycloak fonctionne correctement")
