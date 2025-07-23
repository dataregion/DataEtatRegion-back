class AuthenticationError(Exception):
    """Exception en cas de problème lié à l'authentification"""
    pass


class InvalidTokenError(AuthenticationError):
    """Exception en cas de token non présent"""
    pass

class NoCurrentRegion(InvalidTokenError):
    """Exception en cas de paramètre 'current_region' invalide"""
    pass
