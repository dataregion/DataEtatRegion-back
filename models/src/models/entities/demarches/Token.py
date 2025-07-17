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
    # _token: Column[LargeBinary] = Column("token", LargeBinary, nullable=False)
    uuid_utilisateur: Column[str] = Column(String, nullable=False, index=True)
    enabled: Column[bool] = Column(Boolean, nullable=False, server_default="TRUE")

    # @TODO récupérer le FERNET_SECRET_KEY
    # @property
    # def token(self):
    #     return (
    #         Fernet(current_app.config["FERNET_SECRET_KEY"])
    #         .decrypt(self._token)
    #         .decode("utf-8")
    #     )

    # @token.setter
    # def token(self, value):
    #     self._token = Fernet(current_app.config["FERNET_SECRET_KEY"]).encrypt(
    #         value.encode()
    #     )
