import json
import os
from pathlib import Path

import pytest

from app.services.demarches.tokens import TokenService
from models.entities.demarches.Token import Token

_data = Path(os.path.dirname(__file__)) / "data"


@pytest.fixture(scope="function")
def init_tokens(database):
    tokens = []
    with open(_data / "tokens.json") as file:
        for token in json.load(file):
            token = Token(**token)
            tokens.append(token)
            database.session.add(token)

    database.session.commit()
    yield tokens

    database.session.execute(database.delete(Token))
    database.session.commit()


def test_find_by_uuid_utilisateur(init_tokens):
    tokens_user_1 = TokenService.find_by_uuid_utilisateur("USER1")
    assert len(tokens_user_1) == 1
    assert tokens_user_1[0].token == "TOKEN1"

    TokenService.find_by_uuid_utilisateur("USER2")
    assert len(TokenService.find_by_uuid_utilisateur("USER2")) == 1


def test_find_by_uuid_utilisateur_and_token_id(init_tokens):
    token = TokenService.find_by_uuid_utilisateur_and_token_id("USER1", 101)
    assert token is not None
    assert token.token == "TOKEN1"

    token = TokenService.find_by_uuid_utilisateur_and_token_id("USER2", 102)
    assert token is not None
    assert token.token == "TOKEN2"


def test_create(init_tokens):
    uuid_utilisateur = "USER3"

    token_dto = TokenService.create("TOKEN3", "TOKEN3", uuid_utilisateur)
    token = TokenService.find_by_uuid_utilisateur_and_token_id(uuid_utilisateur, token_dto.id)
    assert token is not None
    assert token.token == "TOKEN3"


def test_update(init_tokens):
    uuid_utilisateur = "TOKEN_TO_UPDATE"
    nom_update = "TOKEN_NOM_UPDATE"
    token_update = "TOKEN_TOKEN_UPDATE"

    token_id = 103
    token_dto = TokenService.update(token_id, nom_update, token_update, uuid_utilisateur)
    token = TokenService.find_by_uuid_utilisateur_and_token_id(uuid_utilisateur, token_dto.id)

    assert token is not None
    assert token.nom == nom_update and token.token == token_update


def test_delete(init_tokens):
    uuid_utilisateur = "TOKEN_TO_DELETE"
    token_id = 104

    assert len(TokenService.find_by_uuid_utilisateur(uuid_utilisateur)) == 1
    TokenService.delete(token_id, uuid_utilisateur)
    assert len(TokenService.find_by_uuid_utilisateur(uuid_utilisateur)) == 0
