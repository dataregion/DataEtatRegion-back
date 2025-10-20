from pydantic import BaseModel


class RedisConnectionInfo(BaseModel):
    host: str
    """Host du serveur redis"""
    port: int
    """Port du serveur redis"""
    db: int
    """Numéro de la base de données redis"""
