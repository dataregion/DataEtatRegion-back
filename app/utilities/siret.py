"""
module de gestion des siret
"""


class SiretFormatError(Exception):
    def __init__(self, message="Le format du numéro SIRET/SIREN est incorrect."):
        self.message = message
        super().__init__(self.message)


class SiretParser:
    """
    Parse un siret ou un siren
    Exceptions:
      SiretFormatError: si le siret / siren n'a pas le bon format
    """

    def __init__(self, siret_ou_siren: str, raise_on_siren=True):
        """
        Initialize the  parser

        Args:
          raise_on_siren (bool): flag pour lever une exception en cas de siren fourni. actif par défaut.
        """
        self._siret = siret_ou_siren
        self._is_siren = False
        self._raise_on_siren = raise_on_siren
        self._validate_siret_ou_siren()

    def _validate_siret_ou_siren(self):
        if not isinstance(self._siret, str):
            raise SiretFormatError("Le numéro SIRET/SIREN doit être une chaine de caractères")

        if not self._siret.isdigit() or (len(self._siret) not in (9, 14)):
            raise SiretFormatError("Le numéro SIRET/SIREN doit être une chaîne de 9 ou 14 chiffres.")

        self._is_siren = len(self._siret) == 9

        if self._raise_on_siren and self._is_siren:
            raise SiretFormatError("Le numéro doit être un SIRET")

        if self._is_siren:
            self._siret = f"{self._siret}00000"

    @property
    def is_siren(self):
        return self._is_siren

    @property
    def siret(self):
        """Renvoie un siret - complèté par des 0 si un siren a été renseigné"""
        return self._siret

    @property
    def siren(self):
        """Renvoie la partie siren."""
        return self._siret[0:9]
