from http import HTTPStatus
import logging

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from apis.apps.budget.services.colonnes import (
    get_list_colonnes_grouping,
    get_list_colonnes_tableau,
)
from apis.database import get_db
from apis.security import ConnectedUser, get_connected_user
from apis.shared.decorators import handle_exceptions
from apis.shared.models import APISuccess


router = APIRouter()
logger = logging.getLogger(__name__)

@router.get("/tableau", summary="Liste des colonnes possibles pour le tableau")
@handle_exceptions
def get_colonnes_tableau(user: ConnectedUser = Depends(get_connected_user), db: Session = Depends(get_db)):
    logging.debug("[PREFERENCE][CTRL] Post users prefs")
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des colonnes disponibles pour le tableau",
        data=[c.to_dict() for c in get_list_colonnes_tableau()],
    ).to_json_response()

@router.get("/grouping", summary="Liste des colonnes possibles pour le grouping")
@handle_exceptions
def get_colonnes_grouping(user: ConnectedUser = Depends(get_connected_user), db: Session = Depends(get_db)):
    return APISuccess(
        code=HTTPStatus.OK,
        message="Liste des colonnes disponibles pour le grouping",
        data=[c.to_dict() for c in get_list_colonnes_grouping()],
    ).to_json_response()
