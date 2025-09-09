from contextlib import contextmanager
from unittest.mock import patch


@contextmanager
def patching_roles(roles=None):
    if roles is None:
        roles = ["ADMIN"]

    class _Mocked:
        @property
        def roles(self):
            return roles

        @property
        def current_region(self):
            return "053"

        @property
        def username(self):
            return "user@domain.fr"

        @property
        def azp(self):
            return "bretagne.budget"

    patch_loc1 = "app.servicesapp.authentication.connected_user._current_connected_user"

    with patch(patch_loc1, return_value=_Mocked()):
        yield
