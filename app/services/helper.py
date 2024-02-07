from abc import ABCMeta, abstractmethod
from typing import TypeVar, Generic

from sqlalchemy import Column

from app.models.enums.TypeCodeGeo import TypeCodeGeo
from app.models.financial.France2030 import France2030
from app.models.refs.commune import Commune
from app.models.refs.siret import Siret


T = TypeVar("T")


class TypeCodeGeoToSqlAlchemyColumnResolver(Generic[T], metaclass=ABCMeta):
    """
    Classe qui résoud la colonne à utiliser pour filtrer le code geo
    dépendant du TypeCodeGeo ainsi que du modèle utilisé.
    """

    def __init__(self, model: type[T]):
        self._model = model

    @abstractmethod
    def code_geo_column(self, type_geo: TypeCodeGeo) -> Column[str]:
        pass


class TypeCodeGeoToFrance2030CodeGeoResolver(TypeCodeGeoToSqlAlchemyColumnResolver[France2030]):
    def __init__(self):
        super().__init__(France2030)

    def code_geo_column(self, niveau_geo: TypeCodeGeo | str) -> Column[str]:
        if isinstance(niveau_geo, str):
            type_geo = TypeCodeGeo[niveau_geo.upper()]
        else:
            type_geo = niveau_geo

        beneficiaire: type[Siret] = self._model.beneficiaire.property.mapper.class_
        commune: type[Commune] = beneficiaire.ref_commune.property.mapper.class_
        column = commune.code
        match type_geo:
            case TypeCodeGeo.REGION:
                column = commune.code_region
            case TypeCodeGeo.DEPARTEMENT:
                column = commune.code_departement
            case TypeCodeGeo.EPCI:
                column = commune.code_epci
            case TypeCodeGeo.CRTE:
                column = commune.code_crte
            case TypeCodeGeo.ARRONDISSEMENT:
                column = commune.code_arrondissement
            case TypeCodeGeo.QPV:
                column = beneficiaire.code_qpv

        return column
