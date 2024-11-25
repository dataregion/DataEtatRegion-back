from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer


from abc import abstractmethod


class FinancialData(_Audit):
    # PK
    id = Column(Integer, primary_key=True)

    def __setattr__(self, key, value):
        if (
            (key == "centre_couts" or key == "referentiel_programmation")
            and isinstance(value, str)
            and value.startswith("BG00/")
        ):
            value = value[5:]
        if key == "montant":
            value = float(str(value).replace("\U00002013", "-").replace(",", "."))

        if key == "contrat_etat_region" or key == "siret":
            value = self._fix_sharp(value)

        if key == "siret" and value is not None:
            value = self._fix_length_siret(value)

        if key == "programme" and isinstance(value, str) and value.startswith("0"):
            value = value[1:]

        super().__setattr__(key, value)

    def update_attribute(self, data: dict):
        """
        update instance chorus avec les infos d'une ligne issue d'un fichier chorus
        :param data:
        :return:
        """

        for key, value in data.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @abstractmethod
    def should_update(self, new_financial: dict) -> bool:
        pass

    @staticmethod
    def _fix_sharp(value: str) -> str:
        # CHAMP VIDE
        if value == "#":
            return None

        return value

    @staticmethod
    def _fix_length_siret(value: str) -> str:
        # SIRET VIDE
        if len(value) < 14:
            nb_zeros_a_ajouter = 14 - len(value)
            value = "0" * nb_zeros_a_ajouter + str(value)

        return value
