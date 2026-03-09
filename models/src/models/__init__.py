from sqlalchemy.orm import declarative_base
import logging

logger = logging.getLogger(__name__)

Base = None


def _PersistenceBaseModelInstance():
    """The base model class setup for this module"""
    global Base
    if Base is None:
        raise Exception("Module is not initialized correcly, please use init function")
    return Base


def init(base=None):
    """Initialise le module persistence en utilisant une classe de base pour les modèles SA"""
    global Base

    if base is None and Base is not None:
        logger.debug("Persistence module already initialized, keeping existing Base")
    elif base is None:
        logger.info("Using default vanilla SQLAlchemy configuration")
        Base = declarative_base()
    elif base is not None:
        logger.info("Using custom base.")
        Base = base
