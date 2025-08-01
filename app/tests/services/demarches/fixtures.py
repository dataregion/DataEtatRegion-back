import os
from flask import current_app
from pathlib import Path
import pytest
import json

from models.entities.demarches.Token import Token

_data = Path(os.path.dirname(__file__)) / "data"


@pytest.fixture(scope="function")
def fernet_key():
    secret_key = current_app.config["FERNET_SECRET_KEY"]
    return secret_key


@pytest.fixture(scope="function")
def init_tokens(database, fernet_key):
    tokens = []

    with open(_data / "tokens.json") as file:
        for token in json.load(file):
            token = Token.make_from_kwargs(fernet_key, **token)
            tokens.append(token)
            database.session.add(token)

    database.session.commit()
    yield tokens

    database.session.execute(database.delete(Token))
    database.session.commit()
