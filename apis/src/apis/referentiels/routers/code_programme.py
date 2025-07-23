from fastapi import Depends
from requests import Session

from models.entities.refs.CodeProgramme import CodeProgramme
from models.schemas.refs import CodeProgrammeSchema

from apis.budget.models.budget_query_params import V3QueryParams
from apis.database import get_db
from apis.referentiels.services.referentiels_router_factory import create_referentiel_router


router = create_referentiel_router(CodeProgramme, CodeProgrammeSchema, "programmes")
