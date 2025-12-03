from models.entities.refs import Commune, Qpv
from models.entities.refs.QpvCommune import QpvCommune
from sqlalchemy import select
from sqlalchemy.orm.session import Session

from models.entities.financial.query.FlattenFinancialLinesDataQpv import (
    FlattenFinancialLinesDataQPV as FinancialLinesDataQPV,
)
from models.value_objects.common import TypeCodeGeo

from services.qpv.query_params import QpvQueryParams
from services.shared.financial_line_query_builder import FinancialLineQueryBuilder


class QpvQueryBuilder(FinancialLineQueryBuilder):
    """
    Constructeur de requête SQLAlchemy pour la vue budget
    """

    def __init__(self, session: Session, params: QpvQueryParams) -> None:
        super().__init__(FinancialLinesDataQPV, session, params)

    """
    Méthodes de conditions spécifiques aux requêtes de Data QPV
    """

    def where_geo_loc_qpv(self, type_geo: TypeCodeGeo, list_code_geo: list[str], source_region: str):
        if list_code_geo is None:
            return self

        # Protection contre les types géo encore non gérés
        if type_geo not in [
            TypeCodeGeo.DEPARTEMENT,
            TypeCodeGeo.EPCI,
            TypeCodeGeo.COMMUNE,
        ]:
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
