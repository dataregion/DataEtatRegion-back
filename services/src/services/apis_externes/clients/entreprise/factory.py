from api_entreprise import ApiEntreprise, ContextInfo, Config

from models.value_objects.api_entreprise_info import ApiEntrepriseInfo

from models.value_objects.ratelimiter_info import RateLimiterInfo


def make_api_entreprise(
    api_entrepise_info: ApiEntrepriseInfo, rate_limiter_info: RateLimiterInfo
) -> ApiEntreprise | None:
    """Fabrique un client API"""
    timeout = 5

    url = api_entrepise_info.url
    token = api_entrepise_info.token
    context = api_entrepise_info.context
    recipient = api_entrepise_info.recipient
    object = api_entrepise_info.object

    timeout = api_entrepise_info.timeout_seconds or timeout

    api_config = Config(
        url,
        token,
        ContextInfo(context=context, recipient=recipient, object=object),
        rate_limiter=None,
    )
    api_config.timeout_s = timeout

    return ApiEntreprise(api_config)
