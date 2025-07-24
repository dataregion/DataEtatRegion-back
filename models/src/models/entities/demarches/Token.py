from dataclasses import dataclass

from cryptography.fernet import Fernet

# from flask import current_app
from sqlalchemy import Boolean, Column, String, Integer, LargeBinary
from models import _PersistenceBaseModelInstance

# from app import db


@dataclass
class Token(_PersistenceBaseModelInstance()):
    """
    Modèle pour stocker les tokens d'accès à DS
    """

    __tablename__ = "tokens"
    __bind_key__ = "demarches_simplifiees"

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)
    nom: Column[str] = Column(String, nullable=False)
    _token: Column[LargeBinary] = Column("token", LargeBinary, nullable=False)
    uuid_utilisateur: Column[str] = Column(String, nullable=False, index=True)
    enabled: Column[bool] = Column(Boolean, nullable=False, server_default="TRUE")

    def get_token(self, fernet_key: str) -> str:
        return Fernet(fernet_key).decrypt(self._token).decode("utf-8")

    def set_token(self, value: str, fernet_key: str):
        self._token = Fernet(fernet_key).encrypt(value.encode("utf-8"))
