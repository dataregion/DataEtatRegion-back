from sqlalchemy import (
    Column,
    func,
    literal,
    or_,
)
from sqlalchemy.orm.session import Session

from models.entities.common.Tags import Tags
from models.entities.financial.query.FlattenFinancialLinesDataQpv import (
    EnrichedFlattenFinancialLinesDataQPV as FinancialLinesDataQPV,
)
from models.value_objects.common import DataType, TypeCodeGeo
from models.value_objects.tags import TagVO
from services.helper import (
    TypeCodeGeoToFinancialLineLocInterministerielleCodeGeoResolver,
)
from services.helper import TypeCodeGeoToFinancialLineBeneficiaireCodeGeoResolver

from apis.apps.qpv.models.qpv_query_params import QpvQueryParams, SourcesQueryParams
from apis.shared.enums import BenefOrLoc
from apis.shared.query_builder import V3QueryBuilder


class SourcesQueryBuilder(V3QueryBuilder[FinancialLinesDataQPV]):
    def __init__(self, session: Session, params: SourcesQueryParams) -> None:
        super().__init__(FinancialLinesDataQPV, session, params)

    def source_is(self, source: DataType | str | None = None):
        if source is not None:
            self._query = self._query.where(FinancialLinesDataQPV.source == source)
        return self

    def source_region_in(self, source_region: list[str] | None, can_be_null: bool = True):
        """Filtre sur la source region. Notons que ce filtre est passant sur les lignes sans source regions"""
        self.where_field_in(FinancialLinesDataQPV.source_region, source_region, can_be_null=can_be_null)
        return self

    def data_source_is(self, data_source: str | None = None):
        self.where_field_in(FinancialLinesDataQPV.data_source, [data_source], can_be_null=True)
        return self

    def par_identifiant_technique(self, source: DataType, id: int):
        """Filtre selon l'identifiant technique. ie couple source - id"""
        self._query = self._query.where(FinancialLinesDataQPV.source == str(source.value), FinancialLinesDataQPV.id == id)
        return self


class QpvQueryBuilder(SourcesQueryBuilder):
    """
    Constructeur de requête SQLAlchemy pour la vue budget
    """

    def __init__(self, session: Session, params: QpvQueryParams) -> None:
        super().__init__(session, params)

        self.__init_resolvers__()

    def __init_resolvers__(self):
        self._code_geo_column_locinterministerielle_resolver = (
            TypeCodeGeoToFinancialLineLocInterministerielleCodeGeoResolver()
        )
        self._code_geo_column_benef_resolver = TypeCodeGeoToFinancialLineBeneficiaireCodeGeoResolver()


    """
    Méthodes de création de conditions
    """

    def code_programme_in(self, codes_programme: list[str] | None = None):
        self.where_field_in(FinancialLinesDataQPV.programme_code, codes_programme)
        return self

    def code_programme_not_in(self, codes_programme: list[str] | None = None):
        self.where_field_not_in(FinancialLinesDataQPV.programme_code, codes_programme)
        return self

    def annee_in(self, annees: list[int] | None):
        self.where_field_in(FinancialLinesDataQPV.annee, annees)
        return self

    def niveau_code_geo_in(self, niveau_geo: str | None, code_geo: list | None, source_region: str):
        if niveau_geo is not None and code_geo is not None:
            self.where_geo(TypeCodeGeo[niveau_geo.upper()], code_geo, source_region)
        return self

    def lieu_action_code_qpv_in(self, code_qpv: list | None, source_region: str):
        if code_qpv is not None:
            self.where_geo_loc_qpv(2024, code_qpv, source_region)
        else:
            self.where_qpv_not_null(FinancialLinesDataQPV.lieu_action_code_qpv)
        return self

    def centres_couts_in(self, centres_couts: list[str] | None):
        self.where_field_in(FinancialLinesDataQPV.centreCouts_code, centres_couts)
        return self

    def themes_in(self, themes: list[str] | None = None):
        self.where_field_in(FinancialLinesDataQPV.programme_theme, themes)
        return self

    def beneficiaire_siret_in(self, sirets: list[str] | None = None):
        self.where_field_in(FinancialLinesDataQPV.beneficiaire_code, sirets)
        return self

    def categorie_juridique_in(
        self,
        types_beneficiaires: list[str] | None,
        includes_none: bool = False,
    ):
        conds = []
        if types_beneficiaires is not None and includes_none:
            conds.append(FinancialLinesDataQPV.beneficiaire_categorieJuridique_type)

        if types_beneficiaires is not None:
            conds.append(FinancialLinesDataQPV.beneficiaire_categorieJuridique_type.in_(types_beneficiaires))

        cond = or_(*conds)
        self._query = self._query.where(cond)
        return self

    def where_qpv_not_null(self, field: Column):
        field = FinancialLinesDataQPV.lieu_action_code_qpv
        self._query = self._query.where(
            FinancialLinesDataQPV.source == DataType.FINANCIAL_DATA_AE,
            field != None,  # noqa: E711
        )
        return self

    def where_geo_loc_qpv(self, type_geo: TypeCodeGeo, list_code_geo: list[str], source_region: str):
        if list_code_geo is None:
            return self

        self._where_geo(
            type_geo,
            list_code_geo,
            source_region,
            None,
            FinancialLinesDataQPV.lieu_action_code_qpv,
            BenefOrLoc.LOCALISATION_QPV,
        )
        return self

    def where_geo(
        self,
        type_geo: TypeCodeGeo,
        list_code_geo: list[str],
        source_region: str,
        benef_or_loc: BenefOrLoc | None = None,
    ):
        if list_code_geo is None:
            return self

        column_codegeo_commune_loc_inter = self._code_geo_column_locinterministerielle_resolver.code_geo_column(
            type_geo
        )
        column_codegeo_commune_beneficiaire = self._code_geo_column_benef_resolver.code_geo_column(type_geo)

        self._where_geo(
            type_geo,
            list_code_geo,
            source_region,
            column_codegeo_commune_loc_inter,
            column_codegeo_commune_beneficiaire,
            benef_or_loc,
        )
        return self

    def _where_geo(
        self,
        type_geo: TypeCodeGeo,
        list_code_geo: list[str],
        source_region: str,
        column_codegeo_commune_loc_inter: Column[str] | None,
        column_codegeo_commune_beneficiaire: Column[str] | None,
        benef_or_loc: BenefOrLoc | None = None,
    ):
        conds = []

        #
        # On calcule les patterns valides pour les codes de localisations interministerielles
        #
        if benef_or_loc is None or benef_or_loc is BenefOrLoc.LOCALISATION_INTER:
            # Calcule les codes de la localisation interministerielle suivant le code geographique
            code_locinter_pattern = []
            if type_geo is TypeCodeGeo.REGION:
                code_locinter_pattern = [f"N{code}" for code in list_code_geo]
            elif type_geo is TypeCodeGeo.DEPARTEMENT:
                code_locinter_pattern = [f"N{source_region}{code}" for code in list_code_geo]
            # fmt:off
            _conds_code_locinter = [
                FinancialLinesDataQPV.localisationInterministerielle_code.ilike(f"{pattern}%")
                for pattern
                in code_locinter_pattern
            ]
            # fmt:on
            if len(code_locinter_pattern) > 0:
                conds.append(or_(*_conds_code_locinter))

        #
        # Ou les code geo de la commune associée à la localisation interministerielle
        #
        if column_codegeo_commune_loc_inter is not None and (
            benef_or_loc is None or benef_or_loc == BenefOrLoc.LOCALISATION_INTER
        ):
            conds.append(column_codegeo_commune_loc_inter.in_(list_code_geo))

        #
        # Ou les code geo de la commune associée au bénéficiaire
        #
        if column_codegeo_commune_beneficiaire is not None and (
            benef_or_loc is None
            or benef_or_loc == BenefOrLoc.BENEFICIAIRE
            or benef_or_loc == BenefOrLoc.LOCALISATION_QPV
        ):
            conds.append(column_codegeo_commune_beneficiaire.in_(list_code_geo))

        where_clause = or_(*conds)
        self._query = self._query.where(where_clause)
        return self._query
