from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer


from abc import abstractmethod


class FinancialData(_Audit):
    # PK
    id = Column(Integer, primary_key=True)

    def __setattr__(self, key, value):
       # Gestion des centres de coûts et référentiels de programmation
        if key in {"centre_couts", "referentiel_programmation"} and isinstance(value, str) and value.startswith("BG00/"):
            value = value[5:]

        # Conversion des montants
        elif key == "montant":
            value = float(str(value).replace("\u2013", "-").replace(",", "."))  # Remplace le tiret Unicode et la virgule

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
        elif key in {"tranche_fonctionnelle", "fonds","projet_analytique","axe_ministeriel_1","axe_ministeriel_2","centre_financier","type_piece"} and value == "":
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
