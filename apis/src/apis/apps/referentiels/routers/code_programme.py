import logging

from models.entities.refs.CodeProgramme import CodeProgramme
from models.schemas.refs import CodeProgrammeSchema

from apis.apps.referentiels.services.referentiels_router_factory import create_referentiel_router


logger = logging.getLogger(__name__)
router = create_referentiel_router(CodeProgramme, CodeProgrammeSchema, logger, "programmes")
