from typing import TypeVar
from models.connected_user import ConnectedUser

from services.shared.source_query_params import SourcesQueryParams

_params_T = TypeVar("_params_T", bound=SourcesQueryParams)


def enforce_query_params_with_connected_user_rights(params: _params_T, user: ConnectedUser) -> _params_T:
    """Replace les paramètres en premier argument avec la source_region / data_source de la connexion utilisateur"""
    if user.current_region != "NAT":
        params = params.with_update(update={"source_region": user.current_region})
    else:
        params = params.with_update(update={"data_source": "NATION"})
    return params
