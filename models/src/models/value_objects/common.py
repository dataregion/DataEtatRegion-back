from enum import Enum


class DataType(Enum):
    FINANCIAL_DATA_AE = "FINANCIAL_DATA_AE"
    FINANCIAL_DATA_CP = "FINANCIAL_DATA_CP"
    FRANCE_RELANCE = "FRANCE_RELANCE"
    FRANCE_2030 = "FRANCE_2030"
    ADEME = "ADEME"
    REFERENTIEL = "REFERENTIEL"


class TypeCodeGeo(Enum):
    """
    Liste des code geo possible
    """

    REGION = "REGION"
    ARRONDISSEMENT = "ARRONDISSEMENT"
    CRTE = "CRTE"
    COMMUNE = "COMMUNE"
    EPCI = "EPCI"
    DEPARTEMENT = "DEPARTEMENT"
    QPV = "QPV"
    QPV24 = "QPV24"


class BenefOrLoc(Enum):
    BENEFICIAIRE = "beneficiaire"
    LOCALISATION_INTER = "localisationInterministerielle"
    LOCALISATION_QPV = "localisation_action_qpv"
