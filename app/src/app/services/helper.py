from abc import ABCMeta, abstractmethod

from sqlalchemy import Column

from models.value_objects.common import TypeCodeGeo
from models.entities.financial.France2030 import France2030
from models.entities.refs.Commune import Commune
from models.entities.refs.Siret import Siret

from models.entities.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLines as FinancialLines


class TypeCodeGeoToSqlAlchemyColumnResolver(metaclass=ABCMeta):
    """
    Classe qui résoud la colonne à utiliser pour filtrer le code geo
    dépendant du TypeCodeGeo ainsi que du modèle utilisé.
    """

    @abstractmethod
    def code_geo_column(self, type_geo: TypeCodeGeo) -> Column[str] | None:
        pass

    def parse_niveau_geo(self, niveau_geo: TypeCodeGeo | str) -> TypeCodeGeo:
        if isinstance(niveau_geo, str):
            type_geo = TypeCodeGeo[niveau_geo.upper()]
        else:
            type_geo = niveau_geo
        return type_geo


class TypeCodeGeoToFrance2030CodeGeoResolver(TypeCodeGeoToSqlAlchemyColumnResolver):
    def code_geo_column(self, niveau_geo: TypeCodeGeo | str) -> Column[str] | None:
        type_geo = self.parse_niveau_geo(niveau_geo)

        beneficiaire: type[Siret] = France2030.beneficiaire.property.mapper.class_
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


class TypeCodeGeoToFinancialLineLocInterministerielleCodeGeoResolver(TypeCodeGeoToSqlAlchemyColumnResolver):
    def code_geo_column(self, niveau_geo: TypeCodeGeo | str) -> Column[str] | None:
        type_geo = self.parse_niveau_geo(niveau_geo)

        column = None

        match type_geo:
            case TypeCodeGeo.REGION:
                column = FinancialLines.localisationInterministerielle_commune_codeRegion
            case TypeCodeGeo.DEPARTEMENT:
                column = FinancialLines.localisationInterministerielle_commune_codeDepartement
            case TypeCodeGeo.EPCI:
                column = FinancialLines.localisationInterministerielle_commune_codeEpci
            case TypeCodeGeo.CRTE:
                column = FinancialLines.localisationInterministerielle_commune_codeCrte
            case TypeCodeGeo.ARRONDISSEMENT:
                column = FinancialLines.localisationInterministerielle_commune_arrondissement_code
            case TypeCodeGeo.COMMUNE:
                column = FinancialLines.localisationInterministerielle_commune_code

        return column


class TypeCodeGeoToFinancialLineBeneficiaireCodeGeoResolver(TypeCodeGeoToSqlAlchemyColumnResolver):
    def code_geo_column(self, niveau_geo: TypeCodeGeo | str) -> Column[str] | None:
        type_geo = self.parse_niveau_geo(niveau_geo)

        column = FinancialLines.beneficiaire_commune_code

        match type_geo:
            case TypeCodeGeo.REGION:
                column = FinancialLines.beneficiaire_commune_codeRegion
            case TypeCodeGeo.DEPARTEMENT:
                column = FinancialLines.beneficiaire_commune_codeDepartement
            case TypeCodeGeo.EPCI:
                column = FinancialLines.beneficiaire_commune_codeEpci
            case TypeCodeGeo.CRTE:
                column = FinancialLines.beneficiaire_commune_codeCrte
            case TypeCodeGeo.ARRONDISSEMENT:
                column = FinancialLines.beneficiaire_commune_arrondissement_code
            case TypeCodeGeo.QPV:
                column = FinancialLines.beneficiaire_qpv_code

        return column
