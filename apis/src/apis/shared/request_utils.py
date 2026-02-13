"""Utilitaires pour les requêtes HTTP FastAPI."""

from fastapi import Request


def get_origin_referrer(request: Request) -> str:
    """Récupère l'origine de la requête (pour les emails de partage).

    Args:
        request: Objet Request FastAPI

    Returns:
        L'origine de la requête (header origin ou base_url)
    """
    origin = request.headers.get("origin")
    if origin and "localhost" not in origin:
        return origin
    return str(request.base_url).rstrip("/")
