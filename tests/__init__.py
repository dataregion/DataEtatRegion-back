import os
from functools import wraps
from unittest.mock import patch
from pathlib import Path

TESTS_PATH = Path(os.path.dirname(__file__))


# MOCK du accept_token
def mock_accept_token(*args, **kwargs):
    def wrapper(view_func):
        @wraps(view_func)
        def decorated(*args, **kwargs):
            return view_func(*args, **kwargs)

        return decorated

    return wrapper


patch("flask_pyoidc.OIDCAuthentication.token_auth", mock_accept_token).start()
