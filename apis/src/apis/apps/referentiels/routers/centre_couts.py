import logging
from typing import Annotated

from apis.services.model.pydantic_annotation import make_pydantic_annotation_from_marshmallow
from apis.shared.models import APISuccess
from models.entities.refs.CentreCouts import CentreCouts as CentreCoutsFlask
from models.schemas.refs import CentreCoutsSchema

from apis.apps.referentiels.services.referentiels_router_factory import (
    create_referentiel_router,
)
from apis.security.keycloak_token_validator import KeycloakTokenValidator


PydanticCentreCoutsModel = make_pydantic_annotation_from_marshmallow(CentreCoutsSchema)
CentreCouts = Annotated[CentreCoutsFlask, PydanticCentreCoutsModel]


class CentreCoutsResponse(APISuccess[list[CentreCouts]]):
    pass


logger = logging.getLogger(__name__)
keycloak_validator = KeycloakTokenValidator.get_application_instance()
router = create_referentiel_router(
    CentreCouts, CentreCoutsSchema, CentreCoutsResponse, keycloak_validator, logger, "centre-couts"
)
