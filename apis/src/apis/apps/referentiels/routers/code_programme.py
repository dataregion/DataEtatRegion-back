import logging
from typing import Annotated

from apis.services.model.pydantic_annotation import make_pydantic_regles_from_marshmallow
from apis.shared.models import APISuccess
from models.entities.refs.CodeProgramme import CodeProgramme as CodeProgrammeFlask
from models.schemas.refs import CodeProgrammeSchema

from apis.apps.referentiels.services.referentiels_router_factory import (
    create_referentiel_router,
)
from apis.security.keycloak_token_validator import KeycloakTokenValidator


PydanticCodeProgrammeModel = make_pydantic_regles_from_marshmallow(CodeProgrammeSchema, False)
CodeProgramme = Annotated[CodeProgrammeFlask, PydanticCodeProgrammeModel]


class ProgrammeResponse(APISuccess[list[CodeProgramme]]):
    pass


logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()
router = create_referentiel_router(
    CodeProgramme, CodeProgrammeSchema, ProgrammeResponse, keycloak_validator, logger, "programmes"
)
