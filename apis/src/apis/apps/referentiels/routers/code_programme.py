import logging

from models.entities.refs.CodeProgramme import CodeProgramme
from models.schemas.refs import CodeProgrammeSchema

from apis.apps.referentiels.services.referentiels_router_factory import (
    create_referentiel_router,
)
from apis.config.current import get_config
from apis.security.keycloak_token_validator import KeycloakTokenValidator


logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator(get_config())
router = create_referentiel_router(
    CodeProgramme, CodeProgrammeSchema, keycloak_validator, logger, "programmes"
)
