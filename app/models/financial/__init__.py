from abc import abstractmethod
from app.models.common.Audit import Audit
from marshmallow import fields

__all__ = (
    "FinancialData",
    "MontantFinancialAe",
    "FinancialCp",
    "FinancialAe",
    "Ademe",
    "France2030",
)

from app.models.refs.siret import Siret


class FinancialData(Audit):
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


class CommonField(fields.Field):
    def _jsonschema_type_mapping(self):
        """
        Retourne un jsonchema object contenant code et label
        :return:
        """
        return {"type": "object", "properties": {"label": {"type": "string"}, "code": {"type": "string"}}}


class CommuneField(fields.Field):
    """Field Commune"""

    def _jsonschema_type_mapping(self):
        return {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "label": {"type": "string"},
                "code_region": {"type": "string"},
                "label_region": {"type": "string"},
                "code_departement": {"type": "string"},
                "label_departement": {"type": "string"},
                "code_epci": {"type": "string"},
                "label_epci": {"type": "string"},
                "code_crte": {"type": "string"},
                "label_crte": {"type": "string"},
                "arrondissement": {"type": "object", "nullable": True},
            },
        }

    def _serialize(self, value: Siret, attr, obj, **kwargs):
        if value is None:
            return {}
        return {
            "code": value.ref_commune.code,
            "label": value.ref_commune.label_commune,
            "code_region": value.ref_commune.code_region,
            "label_region": value.ref_commune.label_region,
            "code_departement": value.ref_commune.code_departement,
            "label_departement": value.ref_commune.label_departement,
            "code_epci": value.ref_commune.code_epci,
            "label_epci": value.ref_commune.label_epci,
            "code_crte": value.ref_commune.code_crte,
            "label_crte": value.ref_commune.label_crte,
            "arrondissement": {
                "code": value.ref_commune.ref_arrondissement.code,
                "label": value.ref_commune.ref_arrondissement.label,
            }
            if value.ref_commune.ref_arrondissement is not None
            else None,
        }
