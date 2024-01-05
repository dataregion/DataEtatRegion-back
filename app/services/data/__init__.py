"""
Services liés à la couche d'accès aux données
"""

from sqlalchemy import Column, ColumnExpressionArgument, Select, desc, select, or_, func, distinct
from app.models.enums.DataType import DataType
from app.models.enums.TypeCodeGeo import TypeCodeGeo
from app.database import db

from app.models.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLines as FinancialLines
from app.models.tags.Tags import TagVO, Tags


class BuilderStatementFinancialLine:
    """
    Constructeur de requête SQLAlchemy pour la vue budget
    """

    def __init__(self) -> None:
        stmt: Select = select(FinancialLines)
        self._stmt = stmt

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
        self._stmt_where_field_in(FinancialLines.source_region, source_region)
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

        column_codegeo_commune_loc_inter = None
        column_codegeo_commune_beneficiaire = None
        match type_geo:
            case TypeCodeGeo.REGION:
                column_codegeo_commune_loc_inter = FinancialLines.localisationInterministerielle_commune_codeRegion
                column_codegeo_commune_beneficiaire = FinancialLines.beneficiaire_commune_codeRegion
            case TypeCodeGeo.DEPARTEMENT:
                column_codegeo_commune_loc_inter = FinancialLines.localisationInterministerielle_commune_codeDepartement
                column_codegeo_commune_beneficiaire = FinancialLines.beneficiaire_commune_codeDepartement
            case TypeCodeGeo.EPCI:
                column_codegeo_commune_loc_inter = FinancialLines.localisationInterministerielle_commune_codeEpci
                column_codegeo_commune_beneficiaire = FinancialLines.beneficiaire_commune_codeEpci
            case TypeCodeGeo.CRTE:
                column_codegeo_commune_loc_inter = FinancialLines.localisationInterministerielle_commune_codeCrte
                column_codegeo_commune_beneficiaire = FinancialLines.beneficiaire_commune_codeCrte
            case TypeCodeGeo.ARRONDISSEMENT:
                column_codegeo_commune_loc_inter = (
                    FinancialLines.localisationInterministerielle_commune_arrondissement_code
                )
                column_codegeo_commune_beneficiaire = FinancialLines.beneficiaire_commune_arrondissement_code
            case TypeCodeGeo.QPV:
                column_codegeo_commune_beneficiaire = FinancialLines.beneficiaire_qpv_code
            case _:
                column_codegeo_commune_beneficiaire = FinancialLines.beneficiaire_commune_code
                # return self._where_geo(self._alias_commune_siret.code, Commune.code, list_code_geo)
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

    def _stmt_where_field_in(self, field: Column, set_of_values: list | None):
        if set_of_values is None:
            return

        pruned = [x for x in set_of_values if x is not None]

        if len(pruned) == 0:
            return

        self._stmt = self._stmt.where(field.in_(pruned))

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
