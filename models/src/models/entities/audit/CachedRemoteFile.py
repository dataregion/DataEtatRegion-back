from datetime import datetime

from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, DateTime, Integer, String


class CachedRemoteFile(_Audit, _PersistenceBaseModelInstance()):
    """
    Modèle pour identifier les fichiers téléchargés depuis l'extérieur.
    Avec last_modified et content_length, on détermine si on retraite ou non un fichier.
    """

    __tablename__ = "audit_cached_remote_files"
    __bind_key__ = "audit"

    id: Column[int] = Column(Integer, primary_key=True, nullable=False)
    name: Column[str] = Column(String, nullable=False)
    resource_url: Column[str] = Column(String, nullable=False, unique=True)
    file_path: Column[str] = Column(String, nullable=False, unique=True)
    last_modified: Column[datetime] = Column(DateTime(timezone=True), nullable=True)
    content_length: Column[int] = Column(Integer, nullable=True)
