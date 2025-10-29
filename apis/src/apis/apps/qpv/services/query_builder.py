from models.entities.refs import Commune, Qpv
from models.entities.refs.QpvCommune import QpvCommune
from sqlalchemy import (
    Column,
    func,
    literal,
    or_,
    select,
)
from sqlalchemy.orm.session import Session

from models.entities.common.Tags import Tags
from models.entities.financial.query.FlattenFinancialLinesDataQpv import (
    EnrichedFlattenFinancialLinesDataQPV as FinancialLinesDataQPV,
)
from models.value_objects.common import DataType, TypeCodeGeo
from models.value_objects.tags import TagVO

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

    def where_geo_loc_qpv(self, type_geo: TypeCodeGeo, list_code_geo: list[str], source_region: str):
        if list_code_geo is None:
            return self
        
        # Protection contre les types géo encore non gérés
        if not type_geo in [TypeCodeGeo.DEPARTEMENT, TypeCodeGeo.EPCI, TypeCodeGeo.COMMUNE]:
            return self
        
        # Récupération des communes
        colonne = Commune.code
        if type_geo == TypeCodeGeo.EPCI:
            colonne = Commune.code_epci
        elif type_geo == TypeCodeGeo.DEPARTEMENT:
            colonne = Commune.code_departement

        # Récupération des QPV concernés
        stmt = (
            select(Qpv.code)
            .join(QpvCommune, Qpv.id == QpvCommune.qpv_id)
            .join(Commune, QpvCommune.commune_id == Commune.id)
            .where(colonne.in_(list_code_geo))
            .distinct()
        )
        codes_qpv = self._session.scalars(stmt).all()

        # Condition sur les codes QPV récupérés
        self._query = self._query.where(FinancialLinesDataQPV.lieu_action_code_qpv.in_(codes_qpv))
        return self

    def lieu_action_code_qpv_in(self, code_qpv: list | None, source_region: str):
        if code_qpv is not None:
            self._query = self._query.where(FinancialLinesDataQPV.lieu_action_code_qpv.in_(code_qpv))
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

