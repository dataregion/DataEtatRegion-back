from fastapi import Depends
from requests import Session

from models.entities.refs.CodeProgramme import CodeProgramme
from models.schemas.refs import CodeProgrammeSchema

from apis.apps.referentiels.services.referentiels_router_factory import create_referentiel_router
from apis.database import get_db


router = create_referentiel_router(CodeProgramme, CodeProgrammeSchema, "programmes")
