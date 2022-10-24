import requests
from nocodb.api import NocoDBAPI
from nocodb.infra.requests_client import NocoDBRequestsClient
from nocodb.nocodb import NocoDBProject, WhereFilter, JWTAuthToken
from typing import Optional

from nocodb.utils import get_query_params


V1_DB_AUTH_API = "api/v1/auth/user/signin"


def get_auth_token(base_uri, email, password) -> JWTAuthToken :
    '''
    Récupéère le token de l'utilisateur technique
    :param base_uri:
    :param email:
    :param password:
    :return:
    '''
    auth_token  = requests.session().post(f'{base_uri}/{V1_DB_AUTH_API}',
                            json=dict(email=email, password=password))
    if auth_token.status_code == 200 :
        return JWTAuthToken(auth_token.json()['token'])


class NocoDBRequestsCustomClient(NocoDBRequestsClient):
    def table_export_csv(
            self,
            project: NocoDBProject,
            table: str,
            filter_obj: Optional[WhereFilter] = None,
            params: Optional[dict] = None,
    ) -> dict:

        response = self._NocoDBRequestsClient__session.get(
            f"{self._NocoDBRequestsClient__api_info.get_table_uri(project, table)}/export/csv",
            params=get_query_params(filter_obj, params),
        )
        return response