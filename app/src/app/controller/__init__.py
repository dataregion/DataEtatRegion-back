from http import HTTPStatus
import logging

from app.exceptions.exceptions import ValidTokenException
from flask import current_app
from sqlalchemy.exc import NoResultFound
from app.controller.utils.Error import ErrorController


@current_app.errorhandler(NoResultFound)
def handle_not_result_found(e):
    return ErrorController("Aucune données n'est présente").to_json(), 404


@current_app.errorhandler(ValidTokenException)
def handle_invalid_token(e: ValidTokenException):
    return ErrorController("Forbidden").to_json(), HTTPStatus.FORBIDDEN


@current_app.errorhandler(Exception)
def handler_exception(error):
    message = None
    if hasattr(error, "message"):
        message = error.message
    logging.exception(error)
    return ErrorController(message).to_json(), 500
