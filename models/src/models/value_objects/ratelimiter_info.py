from .redis_connection_info import RedisConnectionInfo
from pydantic import BaseModel


class RateLimiterInfo(BaseModel):
    """Informations nécessaires pour configurer un client API entreprise."""
    redis: RedisConnectionInfo
    """url du redis"""
    limit: int
    """Limite de requêtes"""
    duration: int
    """Durée en secondes pour la limite de requêtes"""
