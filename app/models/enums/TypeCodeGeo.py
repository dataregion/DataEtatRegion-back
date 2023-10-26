from enum import Enum


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
