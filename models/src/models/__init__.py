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


# def init(base=None):
#     """Initialise le module persistence en utilisant une classe de base pour les modèles SA"""
#     global Base
#     if base is None:
#         logger.info("Using default vanilla SQLAlchemy configuration")
#         Base = declarative_base()
#         return
#     logger.info("Using custom base.")
#     Base = base


def init(base=None):
    """Initialise le module persistence en utilisant une classe de base pour les modèles SA"""
    global Base
    # Si Base est déjà initialisé, ne rien faire (idempotent)
    if Base is not None:
        logger.debug("Base already initialized, skipping")
        return Base
    if base is None:
        logger.info("Using default vanilla SQLAlchemy configuration")
        Base = declarative_base()
        return Base
    logger.info("Using custom base.")
    Base = base
    return Base
