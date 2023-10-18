import dataclasses
from app.models.enums.TypeCodeGeo import TypeCodeGeo


class BadCodeGeoException(Exception):
    message: str

    def __init__(self, message):
        self.message = message
        super().__init__(message)
