"""
Services liés à la couche d'accès aux données
"""

from models.entities.common.Tags import Tags
from sqlalchemy import Column, ColumnExpressionArgument, Select, desc, select, or_, func, distinct
from models.value_objects.common import DataType
from models.value_objects.common import TypeCodeGeo
from app.database import db

from models.entities.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLines as FinancialLines
from models.value_objects.tags import TagVO
from app.services.helper import (
    TypeCodeGeoToFinancialLineBeneficiaireCodeGeoResolver,
    TypeCodeGeoToFinancialLineLocInterministerielleCodeGeoResolver,
)


class BuilderStatementFinancialLine:
    """
    Constructeur de requête SQLAlchemy pour la vue budget
    """

    def __init__(self) -> None:
        stmt: Select = select(FinancialLines)
        self._stmt = stmt

        self._code_geo_column_locinterministerielle_resolver = (
            TypeCodeGeoToFinancialLineLocInterministerielleCodeGeoResolver()
        )
        self._code_geo_column_benef_resolver = TypeCodeGeoToFinancialLineBeneficiaireCodeGeoResolver()

    def n_ej_in(self, n_ej: list[str] | None = None):
        self._stmt_where_field_in(FinancialLines.n_ej, n_ej)
        return self

    def source_is(self, source: str | None = None):
        if source is not None:
            self._stmt = self._stmt.where(FinancialLines.source == source)
        return self

    def themes_in(self, themes: list[str] | None = None):
        self._stmt_where_field_in(FinancialLines.programme_theme, themes)
        return self

    def code_programme_in(self, codes_programme: list[str] | None = None):
        self._stmt_where_field_in(FinancialLines.programme_code, codes_programme)
        return self

    def beneficiaire_siret_in(self, sirets: list[str] | None = None):
        self._stmt_where_field_in(FinancialLines.beneficiaire_code, sirets)
        return self

    def annee_in(self, annees: list[int] | None):
        self._stmt_where_field_in(FinancialLines.annee, annees)
        return self

    def domaine_fonctionnel_in(self, dfs: list[str] | None):
        self._stmt_where_field_in(FinancialLines.domaineFonctionnel_code, dfs)
        return self

    def referentiel_programmation_in(self, ref_prog: list[str] | None):
        self._stmt_where_field_in(FinancialLines.referentielProgrammation_code, ref_prog)
        return self

    def source_region_in(self, source_region: list[str] | None):
        """Filtre sur la source region. Notons que ce filtre est passant sur les lignes sans source regions"""

        self._stmt_where_field_in(FinancialLines.source_region, source_region, can_be_null=True)
        return self

    def type_categorie_juridique_du_beneficiaire_in(
        self,
        types_beneficiaires: list[str] | None,
        includes_none: bool = False,
    ):
        conds = []
        if types_beneficiaires is not None and includes_none:
            _cond = FinancialLines.beneficiaire_categorieJuridique_type == None  # noqa: E711
            conds.append(_cond)

        if types_beneficiaires is not None:
            _cond = FinancialLines.beneficiaire_categorieJuridique_type.in_(types_beneficiaires)
            conds.append(_cond)

        cond = or_(*conds)
        self._stmt = self._stmt.where(cond)
        return self

    def tags_fullname_in(self, fullnames: list[str] | None):
        if fullnames is not None:
            _tags = map(TagVO.sanitize_str, fullnames)
            fullnamein = Tags.fullname.in_(_tags)
            self.where_custom(FinancialLines.tags.any(fullnamein))

        return self

    def ej(self, ej: str, poste_ej: int):
        self._stmt = self._stmt.where(FinancialLines.n_ej == ej).where(FinancialLines.n_poste_ej == poste_ej)
        return self

    def where_geo(self, type_geo: TypeCodeGeo, list_code_geo: list[str], source_region: str):
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
        )
        return self

    def _where_geo(
        self,
        type_geo: TypeCodeGeo,
        list_code_geo: list[str],
        source_region: str,
        column_codegeo_commune_loc_inter: Column[str] | None,
        column_codegeo_commune_beneficiaire: Column[str] | None,
    ):
        conds = []

        #
        # On calcule les patterns valides pour les codes de localisations interministerielles
        #
        code_locinter_pattern = self._codes_locinterministerielle(type_geo, list_code_geo, source_region)
        # fmt:off
        _conds_code_locinter = [
            FinancialLines.localisationInterministerielle_code.ilike(f"{pattern}%") 
            for pattern 
            in code_locinter_pattern
        ]
        # fmt:on
        if len(code_locinter_pattern) > 0:
            conds.append(or_(*_conds_code_locinter))

        #
        # Ou les code geo de la commune associée à la localisation interministerielle
        #
        if column_codegeo_commune_loc_inter is not None:
            conds.append(column_codegeo_commune_loc_inter.in_(list_code_geo))

        #
        # Ou les code geo de la commune associée au bénéficiaire
        #
        if column_codegeo_commune_beneficiaire is not None:
            conds.append(column_codegeo_commune_beneficiaire.in_(list_code_geo))

        where_clause = or_(*conds)
        self._stmt = self._stmt.where(where_clause)
        return self._stmt

    def where_custom(self, where: ColumnExpressionArgument[bool]):
        self._stmt = self._stmt.where(where)
        return self._stmt

    def par_identifiant_technique(self, source: DataType, id: int):
        """Filtre selon l'identifiant technique. ie couple source - id"""
        self._stmt = self._stmt.where(FinancialLines.source == str(source), FinancialLines.id == id)
        return self

    def do_paginate(self, limit, page_number):
        """
        Effectue la pagination des résultats en utilisant les limites spécifiées.
        :param limit: Le nombre maximum d'éléments par page.
        :param page_number: Le numéro de la page.
        :return: L'objet Pagination contenant les résultats paginés.
        """

        return db.paginate(self._stmt, per_page=limit, page=page_number, error_out=False)

    def do_select_annees(self) -> list[int]:
        """
        Retourne l'ensemble des années ordonnées par ordre decroissant
        concernées par la recherche
        """
        subq = select(distinct(FinancialLines.annee)).order_by(desc(FinancialLines.annee)).subquery()
        stmt = select(func.array_agg(subq.c[0]))
        result = db.session.execute(stmt).scalar_one_or_none()
        return result  # type: ignore

    def do_single(self):
        """
        Effectue la recherche et retourne le seul résultat
        :return:
        """
        return db.session.execute(self._stmt).unique().scalar_one_or_none()

    def _stmt_where_field_in(self, field: Column, set_of_values: list | None, can_be_null=False):
        if set_of_values is None:
            return

        pruned = [x for x in set_of_values if x is not None]

        if len(pruned) == 0:
            return

        complete_cond = []

        if can_be_null:
            _cond = field.is_(None)
            complete_cond.append(_cond)

        _cond = field.in_(pruned)
        complete_cond.append(_cond)

        self._stmt = self._stmt.where(or_(*complete_cond))

    def _codes_locinterministerielle(
        self,
        type_geo: TypeCodeGeo,
        list_code_geo: list[str],
        source_region: str,
    ) -> list[str]:
        """Calcule les codes de la localisation interministerielle suivant le code geographique"""
        if type_geo is TypeCodeGeo.REGION:
            return [f"N{code}" for code in list_code_geo]
        elif type_geo is TypeCodeGeo.DEPARTEMENT:
            return [f"N{source_region}{code}" for code in list_code_geo]
        else:
            return []

    def data_source_is(self, data_source: str | None = None):
        if data_source is not None:
            self._stmt = self._stmt.where(
                or_(FinancialLines.data_source == data_source, FinancialLines.data_source.is_(None))
            )
        return self
