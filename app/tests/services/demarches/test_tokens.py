from app.services.demarches.tokens import TokenService
from cryptography.fernet import Fernet
import pytest

from .fixtures import init_tokens, fernet_key

@pytest.fixture
def fernet(fernet_key):
    return Fernet(fernet_key)

def decrypt_token(token: bytes, fernet: Fernet):
    decrypted_token = token
    decrypted_token = fernet.decrypt(decrypted_token) # type: ignore
    decrypted_token = decrypted_token.decode()
    return decrypted_token

def test_find_enabled_by_uuid_utilisateur(fernet, init_tokens):
    tokens_user_1 = TokenService.find_enabled_by_uuid_utilisateur("USER1")
    assert len(tokens_user_1) == 1

    decrypted_token = decrypt_token(tokens_user_1[0]._token, fernet) # type: ignore
    assert decrypted_token == "TOKEN1" # type: ignore

    TokenService.find_enabled_by_uuid_utilisateur("USER2")
    assert len(TokenService.find_enabled_by_uuid_utilisateur("USER2")) == 1


def test_find_by_uuid_utilisateur_and_token_id(init_tokens, fernet):
    token = TokenService.find_by_uuid_utilisateur_and_token_id("USER1", 101)
    assert token is not None
    decrypted_token = decrypt_token(token._token, fernet)
    assert decrypted_token == "TOKEN1"

    token = TokenService.find_by_uuid_utilisateur_and_token_id("USER2", 102)
    assert token is not None
    decrypted_token = decrypt_token(token._token, fernet)
    assert decrypted_token == "TOKEN2"


def test_create(init_tokens, fernet):
    uuid_utilisateur = "USER3"

    token_dto = TokenService.create("TOKEN3", "TOKEN3", uuid_utilisateur)
    token = TokenService.find_by_uuid_utilisateur_and_token_id(uuid_utilisateur, token_dto.id)
    assert token is not None
    assert token.enabled is True
    decrypted_token = decrypt_token(token._token, fernet) # type: ignore
    assert decrypted_token == "TOKEN3"


def test_create_existing(init_tokens, fernet):
    uuid_utilisateur = "USER3"

    token_dto = TokenService.create("TOKEN3", "TOKEN3", uuid_utilisateur)
    token = TokenService.find_by_uuid_utilisateur_and_token_id(uuid_utilisateur, token_dto.id)
    assert token is not None
    decrypted_token = decrypt_token(token._token, fernet)
    assert decrypted_token == "TOKEN3"

    TokenService.delete(token.id, uuid_utilisateur)
    token = TokenService.find_by_uuid_utilisateur_and_token_id(uuid_utilisateur, token_dto.id)
    assert token is not None and token.enabled is False

    token_dto = TokenService.create("TOKEN3", "TOKEN3", uuid_utilisateur)
    token = TokenService.find_by_uuid_utilisateur_and_token_id(uuid_utilisateur, token_dto.id)
    assert token is not None and token.enabled is True


def test_update(init_tokens, fernet):
    uuid_utilisateur = "TOKEN_TO_UPDATE"
    nom_update = "TOKEN_NOM_UPDATE"
    token_update = "TOKEN_TOKEN_UPDATE"

    token_id = 103
    token_dto = TokenService.update(token_id, nom_update, token_update, uuid_utilisateur)
    token = TokenService.find_by_uuid_utilisateur_and_token_id(uuid_utilisateur, token_dto.id)

    assert token is not None
    decrypted_token = decrypt_token(token._token, fernet)
    assert token.nom == nom_update and decrypted_token == token_update


def test_delete(init_tokens):
    uuid_utilisateur = "TOKEN_TO_DELETE"
    token_id = 104

    assert len(TokenService.find_enabled_by_uuid_utilisateur(uuid_utilisateur)) == 1
    TokenService.delete(token_id, uuid_utilisateur)
    tokens = TokenService.find_enabled_by_uuid_utilisateur(uuid_utilisateur)
    assert len(tokens) == 0
    token = TokenService.find_by_uuid_utilisateur_and_token_id(uuid_utilisateur, token_id)
    assert token is not None and token.enabled is False
