from sqlalchemy import or_
from sqlalchemy.orm import Session, DeclarativeBase

from services.shared.financial_line_query_params import FinancialLineQueryParams
from services.shared.source_query_builder import SourcesQueryBuilder


class FinancialLineQueryBuilder(SourcesQueryBuilder):
    """
    Constructeur de requête SQLAlchemy pour la vue budget
    """

    def __init__(
        self,
        model: type[DeclarativeBase],
        session: Session,
        params: FinancialLineQueryParams,
    ) -> None:
        super().__init__(model, session, params)

    """
    Méthodes de création de conditions
    """

    def n_ej_in(self, n_ej: list[str] | None = None):
        self.where_field_in(self._model.n_ej, n_ej)
        return self

    def themes_in(self, themes: list[str] | None = None):
        self.where_field_in(self._model.programme_theme, themes)
        return self

    def code_programme_in(self, codes_programme: list[str] | None = None):
        self.where_field_in(self._model.programme_code, codes_programme)
        return self

    def code_programme_not_in(self, codes_programme: list[str] | None = None):
        self.where_field_not_in(self._model.programme_code, codes_programme)
        return self

    def beneficiaire_siret_in(self, sirets: list[str] | None = None):
        self.where_field_in(self._model.beneficiaire_code, sirets)
        return self

    def annee_in(self, annees: list[int] | None):
        self.where_field_in(self._model.annee, annees)
        return self

    def centres_couts_in(self, centres_couts: list[str] | None):
        self.where_field_in(self._model.centreCouts_code, centres_couts)
        return self

    def domaine_fonctionnel_in(self, dfs: list[str] | None):
        self.where_field_in(self._model.domaineFonctionnel_code, dfs)
        return self

    def referentiel_programmation_in(self, ref_prog: list[str] | None):
        self.where_field_in(self._model.referentielProgrammation_code, ref_prog)
        return self

    def categorie_juridique_in(
        self,
        types_beneficiaires: list[str] | None,
        includes_none: bool = False,
    ):
        conds = []
        if types_beneficiaires is not None and includes_none:
            conds.append(self._model.beneficiaire_categorieJuridique_type)

        if types_beneficiaires is not None:
            conds.append(self._model.beneficiaire_categorieJuridique_type.in_(types_beneficiaires))

        cond = or_(*conds)
        self._query = self._query.where(cond)
        return self

    def ej(self, ej: str, poste_ej: int):
        self._stmt = self._query.where(self._model.n_ej == ej).where(self._model.n_poste_ej == poste_ej)
        return self
