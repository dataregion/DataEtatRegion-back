import logging
import functools

from services.apis_externes.clients.data_subventions.api_subventions import ApiSubventions
from models.value_objects.api_data_subvention_info import ApiDataSubventionInfo


def make_app_api_subventions_client(api_subvention_info: ApiDataSubventionInfo) -> ApiSubventions:
    return ApiSubventions(
        token=api_subvention_info.token,
        url=api_subvention_info.url,
    )
