from http import HTTPStatus
import logging

from app.exceptions.exceptions import DataRegatException, ValidTokenException
from flask import current_app
from sqlalchemy.exc import NoResultFound
from app.controller.utils.Error import ErrorController
from flask_restx import Api


class ApiDataEtat(Api):
    """
    Class Api DataEtat contenant la gestion des erreurs
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._default_error_handler = self.handle_exception

    def handle_exception(self, e):
        """
        Gestionnaire d'exception par défaut pour toutes les API
        Cela peut être un gestionnaire global pour toutes les exceptions.
        """
        # Si l'erreur est déjà gérée, on la renvoie directement
        logging.exception(e)  # Log l'exception
        raise e


def handle_error(error, message, status):
    logging.exception(error)
    return ErrorController(message).to_json(), status


@current_app.errorhandler(NoResultFound)
def handle_not_result_found(e):
    return handle_error(e, "Aucune donnée n'est présente", HTTPStatus.NOT_FOUND)


@current_app.errorhandler(ValidTokenException)
def handle_invalid_token(e: ValidTokenException):
    return handle_error(e, "Forbidden", HTTPStatus.FORBIDDEN)


@current_app.errorhandler(DataRegatException)
def handle_data_regat_exception(e: DataRegatException):
    return handle_error(e, getattr(e, "message", None), HTTPStatus.BAD_REQUEST)


@current_app.errorhandler(Exception)
def handle_generic_exception(e):
    return handle_error(e, getattr(e, "message", None), HTTPStatus.INTERNAL_SERVER_ERROR)
