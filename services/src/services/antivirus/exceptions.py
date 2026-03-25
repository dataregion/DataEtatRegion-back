"""Exceptions propres au service antivirus."""


class AntivirusError(Exception):
    """Exception mère de toutes les erreurs du domaine antivirus."""


class VirusFoundError(AntivirusError):
    """Virus détecté dans le fichier scanné.

    Attributes:
        virus_name: Nom du virus tel que renvoyé par ClamAV.
    """

    def __init__(self, virus_name: str) -> None:
        self.virus_name = virus_name
        super().__init__(f"Virus détecté : {virus_name}")


class AntivirusScanError(AntivirusError):
    """Erreur technique lors du scan (service indisponible, timeout, résultat non conforme…).

    Attributes:
        message: Message destiné à informer l'utilisateur de la raison du rejet.
    """

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)
