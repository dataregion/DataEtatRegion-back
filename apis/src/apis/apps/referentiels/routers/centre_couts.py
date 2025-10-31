import logging

from models.entities.refs.CentreCouts import CentreCouts
from models.schemas.refs import CentreCoutsSchema

from apis.apps.referentiels.services.referentiels_router_factory import (
    create_referentiel_router,
)
from apis.security.keycloak_token_validator import KeycloakTokenValidator


logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()
router = create_referentiel_router(CentreCouts, CentreCoutsSchema, keycloak_validator, logger, "centre-couts")
