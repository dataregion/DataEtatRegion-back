class NiveauCodeGeoException(Exception):
    message: str

    def __init__(self, message):
        self.message = message
        super().__init__(message)
