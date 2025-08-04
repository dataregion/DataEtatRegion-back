from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer


from abc import abstractmethod


class FinancialData(_Audit):
    # PK
    id = Column(Integer, primary_key=True)

    def __setattr__(self, key, value):
        # Gestion des centres de coûts et référentiels de programmation
        if (
            key in {"centre_couts", "referentiel_programmation"}
            and isinstance(value, str)
            and value.startswith("BG00/")
        ):
            value = value[5:]

        # Conversion des montants
        elif key == "montant":
            value = self._convert_montant_float(str(value))

        # Fixation des valeurs pour contrat_etat_region
        elif key == "contrat_etat_region":
            value = self._fix_sharp(value)

        # Fixation de la longueur du siret
        elif key == "siret":
            value = self._fix_sharp(value)
            value = self._fix_length_siret(value) if value is not None else value
        # Suppression du 0 en début de programme
        elif key == "programme" and isinstance(value, str) and value.startswith("0"):
            value = value[1:]

        # Fix des valeur "" à Null
        elif (
            key
            in {
                "tranche_fonctionnelle",
                "fonds",
                "projet_analytique",
                "axe_ministeriel_1",
                "axe_ministeriel_2",
                "centre_financier",
                "type_piece",
            }
            and value == ""
        ):
            value = None

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

    @staticmethod
    def _convert_montant_float(value: str) -> float:
        if value is None:
            return 0.0

        value = value.strip()

        # Remplace les différents types de tirets typographiques par un moins standard
        value = value.replace("\u2013", "-")  # EN DASH
        value = value.replace("\u2212", "-")  # MINUS SIGN
        value = value.replace("\u2014", "-")  # EM DASH

        # Supprime espaces normaux et insécables (séparateurs de milliers)
        value = value.replace("\u202f", "")  # fin insécable
        value = value.replace("\u00a0", "")  # insécable
        value = value.replace(" ", "")  # espace normal

        # Supprime le symbole euro ou autres caractères non numériques
        value = value.replace("€", "")

        # Remplace virgule décimale par point
        value = value.replace(",", ".")

        return float(value)
