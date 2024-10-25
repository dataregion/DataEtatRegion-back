import datetime
import uuid as uuid
from models import _PersistenceBaseModelInstance
from sqlalchemy import Column, ForeignKey, String, Integer, JSON, DateTime, Boolean
from sqlalchemy.orm import relationship


class Preference(_PersistenceBaseModelInstance()):
    __tablename__ = "preference_users"
    __bind_key__ = "settings"
    # PK
    id = Column(Integer, primary_key=True, nullable=False)

    # uuid
    uuid: Column[str] = Column(String(length=36), nullable=False, default=uuid.uuid4)
    # user
    username = Column(String, nullable=False)
    name = Column(String, nullable=False)

    # Url de l'application concerné par la préférence
    application_host = Column(String, nullable=False)

    # Client ID de l'application concernée par la preference
    application_clientid = Column(String, nullable=False)
    # Donnée technique du filtre brut
    filters = Column(JSON, nullable=False)
    # Autre Options pour les preferences (pour les group by par exemple)
    options = Column(JSON, nullable=True)
    # date de creation
    date_creation = Column(DateTime, nullable=True, default=datetime.datetime.utcnow)
    dernier_acces = Column(DateTime, nullable=True)
    nombre_utilisation = Column(Integer, nullable=True, default=0)
    # Relationship
    shares = relationship(
        "Share", lazy="select", uselist=True, cascade="delete,save-update,merge"
    )


class Share(_PersistenceBaseModelInstance()):
    __tablename__ = "share_preference"
    __bind_key__ = "settings"
    # PK
    id = Column(Integer, primary_key=True, nullable=False)

    # FK
    preference_id = Column(Integer, ForeignKey("preference_users.id"))
    shared_username_email = Column(String, nullable=False)
    email_send = Column(Boolean, nullable=False, default=False)
    date_email_send = Column(DateTime, nullable=True)
