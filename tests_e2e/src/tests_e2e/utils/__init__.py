import json
import requests

__all__ = ("call_request",)


def call_request(url, method="GET", json_data=None, headers=None, token=None, params=None):
    """
    Rest call grist
    """
    data = json.dumps(json_data).encode("utf8") if json_data is not None else None

    params = params or {}

    headers = headers or {}

    headers.update(
        {
            "Accept": headers.get("Accept", "application/json"),
            "Content-Type": headers.get("Content-Type", "application/json"),
        }
    )

    # Ajouter l'Authorization si token est fourni
    if token:
        headers["Authorization"] = f"Bearer {token}"

    return requests.request(method, url, data=data, headers=headers, params=params)
