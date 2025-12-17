import functools
from batches.config.current import get_config  # noqa: E402

from gristcli.gristservices.users_grist_service import UserGristDatabaseService, UserScimService, GrisApiService


@functools.cache
def make_or_get_grist_database_service():
    database_url = get_config().grist.database_url
    return UserGristDatabaseService(database_url)


@functools.cache
def make_or_get_user_scim_service():
    server_url = get_config().grist.serveur_url
    token_scim = get_config().grist.token_scim
    return UserScimService(server=server_url, token=token_scim)


def make_grist_api_service(token: str):
    server_url = get_config().grist.serveur_url
    return GrisApiService(server=server_url, token=token)
