from sqlalchemy import Select, or_, Column
from sqlalchemy.orm import selectinload, contains_eager

from .code_geo import BadCodeGeoException
from .. import db
from ..models.enums.TypeCodeGeo import TypeCodeGeo
from ..models.refs.categorie_juridique import CategorieJuridique
from ..models.refs.code_programme import CodeProgramme
from app.models.financial.FinancialAe import FinancialAe as Ae
from app.models.financial.MontantFinancialAe import MontantFinancialAe as MontantAe
from app.models.financial.FinancialCp import FinancialCp as Cp
from ..models.refs.commune import Commune
from ..models.refs.domaine_fonctionnel import DomaineFonctionnel
from ..models.refs.groupe_marchandise import GroupeMarchandise
from ..models.refs.localisation_interministerielle import LocalisationInterministerielle
from ..models.refs.referentiel_programmation import ReferentielProgrammation
from ..models.refs.siret import Siret
from ..models.refs.theme import Theme

__all__ = ("BadCodeGeoException", "BuilderStatementFinancial")


class BuilderStatementFinancial:
    """
    Classe permettant de construire une requête pour récupérer des données à partir de la table FinancialAe.
    """

    _stmt: Select = None

    def __init__(self, stmt=None):
        self._stmt = stmt

    def select_ae(self):
        """
        Spécifie la table et les options de sélection pour la requête.

        :return: L'instance courante de BuilderStatementFinancialAe.
        """
        self._stmt = db.select(Ae).options(
            db.defer(Ae.source_region),
            db.defer(Ae.compte_budgetaire),
            selectinload(Ae.montant_ae).load_only(MontantAe.montant),
            selectinload(Ae.financial_cp).load_only(Cp.montant, Cp.date_derniere_operation_dp),
            selectinload(Ae.tags),
            db.defer(Ae.contrat_etat_region),
        )
        return self

    def join_filter_programme_theme(self, code_programme: list = None, theme: list = None):
        """
        Effectue des jointures avec les tables CodeProgramme et Theme en fonction des codes de programme et des thèmes fournis.

        :param code_programme: Une liste de codes de programme.
        :param theme: Une liste de thèmes.
        :return: L'instance courante de BuilderStatementFinancialAe.
        """
        if code_programme is not None:
            self._stmt = self._stmt.join(Ae.ref_programme.and_(CodeProgramme.code.in_(code_programme))).join(
                CodeProgramme.theme_r, isouter=True
            )
        elif theme is not None:
            self._stmt = self._stmt.join(Ae.ref_programme).join(
                CodeProgramme.theme_r.and_(Theme.label.in_(theme)), isouter=True
            )
        else:
            self._stmt = self._stmt.join(Ae.ref_programme).join(CodeProgramme.theme_r, isouter=True)

        self._stmt = self._stmt.join(Ae.ref_ref_programmation)
        self._stmt = self._stmt.join(Ae.ref_domaine_fonctionnel)
        self._stmt = self._stmt.join(Ae.ref_groupe_marchandise)
        self._stmt = self._stmt.join(Ae.ref_localisation_interministerielle)
        return self

    def join_financial_cp(self):
        """
        Effectue des jointures avec les tables CodeProgramme et Theme en fonction des codes de programme et des thèmes fournis.

        :param code_programme: Une liste de codes de programme.
        :param theme: Une liste de thèmes.
        :return: L'instance courante de BuilderStatementFinancialAe.
        """
        self._stmt = self._stmt.join(Ae.financial_cp)
        return self

    def join_filter_siret(self, siret: list = None):
        """
        Effectue une jointure avec la table Siret en fonction des SIRET fournis.

        :param siret: Une liste de SIRET.
        :return: L'instance courante de BuilderStatementFinancialAe.
        """
        self._stmt = (
            self._stmt.join(Ae.ref_siret.and_(Siret.code.in_(siret))) if siret is not None else self._stmt.join(Siret)
        )
        self._stmt = self._stmt.join(Siret.ref_categorie_juridique)
        return self

    def where_annee(self, annee: list):
        """
        Ajoute une condition WHERE pour filtrer par année.
        :param annee: Une liste d'années.
        :return: L'instance courante de BuilderStatementFinancialAe.
        """
        if annee is not None:
            self._stmt = self._stmt.where(Ae.annee.in_(annee))
        return self

    def where_ej(self, n_ej: str, n_poste_ej: int):
        """
        Ajoute une condition Where pour filter sur le poste_ej et numéro ej
        :param n_ej: le numéro EJ
        :param n_poste_ej:  Le poste ej
        :return:  L'instance courante de BuilderStatementFinancialAe.
        """

        if n_ej is not None and n_poste_ej is not None:
            self._stmt = self._stmt.where(Ae.n_ej == n_ej).where(Ae.n_poste_ej == n_poste_ej)
        return self

    def by_ae_id(self, id: int):
        """
        Sélection uniquement selon l'id technique
        :param id: l'identifiant technique
        :return: L'instance courante de BuilderStatementFinancialAe.
        """
        if id is not None:
            self._stmt = self._stmt.where(Ae.id == id)
        return self

    def join_commune(self):
        """
        Ajoute une jointure simple sur la commune siret
        :return:
        """
        self._stmt = self._stmt.join(Siret.ref_commune)
        return self

    def where_geo_ae(self, type_geo: TypeCodeGeo, list_code_geo: list, source_region: str):
        """
        Ajoute une condition WHERE pour filtrer par géolocalisation sur les engagements

        :param type_geo: Le type de géolocalisation (TypeCodeGeo).
        :param list_code_geo: Une liste de codes géographiques.
        :param source_region: la source region
        :return: L'instance courante de BuilderStatementFinancialAe.
        """
        if list_code_geo is not None:
            self._stmt = self._stmt.join(Siret.ref_commune)
            match type_geo:
                case TypeCodeGeo.DEPARTEMENT:
                    return self._where_geo_departement(list_code_geo, source_region)
                case TypeCodeGeo.EPCI:
                    return self._where_geo(Commune.code_epci, list_code_geo)
                case TypeCodeGeo.CRTE:
                    return self._where_geo(Commune.code_crte, list_code_geo)
                case TypeCodeGeo.ARRONDISSEMENT:
                    return self._where_geo(Commune.code_arrondissement, list_code_geo)
                case TypeCodeGeo.QPV:
                    return self._where_qpv(list_code_geo)
                case _:
                    return self._where_geo(Commune.code, list_code_geo)

        return self

    def where_geo(self, type_geo: TypeCodeGeo, list_code_geo: list):
        """
        Ajoute une condition WHERE pour filtrer par géolocalisation sans les loc interministerielles

        :param type_geo: Le type de géolocalisation (TypeCodeGeo).
        :param list_code_geo: Une liste de codes géographiques.
        :return: L'instance courante de BuilderStatementFinancialAe.
        """
        if list_code_geo is not None:
            self._stmt = self._stmt.join(Siret.ref_commune)

            match type_geo:
                case TypeCodeGeo.DEPARTEMENT:
                    self._stmt = self._stmt.where(Commune.code_departement.in_(list_code_geo))
                case TypeCodeGeo.EPCI:
                    self._stmt = self._stmt.where(Commune.code_epci.in_(list_code_geo))
                case TypeCodeGeo.CRTE:
                    self._stmt = self._stmt.where(Commune.code_crte.in_(list_code_geo))
                case TypeCodeGeo.ARRONDISSEMENT:
                    self._stmt = self._stmt.where(Commune.code_arrondissement.in_(list_code_geo))
                case TypeCodeGeo.QPV:
                    self._where_qpv(list_code_geo)
                case _:
                    self._stmt = self._stmt.where(Commune.code.in_(list_code_geo))

        return self

    def options_select_load(self):
        """
        Ajoute les options de sélection et de chargement des colonnes pour la requête.

        :return: L'instance courante de BuilderStatementFinancialAe.
        """
        self._stmt = self._stmt.options(
            contains_eager(Ae.ref_programme)
            .load_only(CodeProgramme.label)
            .contains_eager(CodeProgramme.theme_r)
            .load_only(Theme.label),
            contains_eager(Ae.ref_ref_programmation).load_only(ReferentielProgrammation.label),
            contains_eager(Ae.ref_groupe_marchandise).load_only(GroupeMarchandise.label),
            contains_eager(Ae.ref_domaine_fonctionnel).load_only(DomaineFonctionnel.label),
            contains_eager(Ae.ref_localisation_interministerielle)
            .load_only(LocalisationInterministerielle.label)
            .contains_eager(LocalisationInterministerielle.commune)
            .load_only(Commune.label_commune, Commune.code),
            contains_eager(Ae.ref_siret)
            .load_only(Siret.code, Siret.denomination)
            .contains_eager(Siret.ref_commune)
            .load_only(Commune.label_commune, Commune.code),
            contains_eager(Ae.ref_siret)
            .contains_eager(Siret.ref_categorie_juridique)
            .load_only(CategorieJuridique.type),
        )
        return self

    def where_custom(self, stmt_where):
        self._stmt = self._stmt.where(stmt_where)
        return self

    def do_paginate(self, limit, page_number):
        """
        Effectue la pagination des résultats en utilisant les limites spécifiées.
        :param limit: Le nombre maximum d'éléments par page.
        :param page_number: Le numéro de la page.
        :return: L'objet Pagination contenant les résultats paginés.
        """
        return db.paginate(self._stmt, per_page=limit, page=page_number, error_out=False)

    def do_single(self):
        """
        Effectue la recherche et retourne le seul résultat
        :return:
        """
        return db.session.execute(self._stmt).scalar_one_or_none()

    def _where_qpv(self, list_code_geo: list):
        """
        Recherche selon le QPV
        :param list_code_geo:
        :return:
        """
        self._stmt = self._stmt.where(Siret.code_qpv.in_(list_code_geo))
        return self

    def _where_geo_departement(self, list_code_geo: list, source_region: str):
        """
        Filtre code geo departement
        :param list_code_geo:
        :param source_region:
        :return:
        """
        subquery = db.select(LocalisationInterministerielle.code).join(LocalisationInterministerielle.commune)
        prefix_code_inter = f"N{source_region}"
        where_clause = []
        for code_geo in list_code_geo:
            where_clause.append(LocalisationInterministerielle.code.ilike(f"{prefix_code_inter}{code_geo}%"))
        subquery = subquery.where(or_(*where_clause)).subquery()
        self._stmt = self._stmt.where(
            Commune.code_departement.in_(list_code_geo) | Ae.localisation_interministerielle.in_(subquery)
        )
        return self

    def _where_geo(self, column: Column, list_code_geo: list):
        """
        Requête de sélection sur les code geo
        :param column: la column de la base
        :param list_code_geo:
        :return:
        """
        subquery = (
            db.select(LocalisationInterministerielle.code)
            .join(LocalisationInterministerielle.commune)
            .where(column.in_(list_code_geo))
            .subquery()
        )
        self._stmt = self._stmt.where(column.in_(list_code_geo) | Ae.localisation_interministerielle.in_(subquery))
        return self


class BuilderStatementFinancialCp:
    """
    Classe permettant de construire une requête pour récupérer des données à partir de la table FinancialCp.
    """

    _stmt: Select = None

    def __init__(self, stmt=None):
        self._stmt = stmt

    def select_cp(self):
        """
        Spécifie la table pour la requête.

        :return: L'instance courante de BuilderStatementFinancialCp.
        """
        self._stmt = db.select(Cp)
        return self

    def by_ae_id(self, id: int):
        """
        Sélection uniquement selon l'id de l'ae
        :param id: l'identifiant de l'ae associée
        :return: L'instance courante de BuilderStatementFinancialCp.
        """
        if id is not None:
            self._stmt = self._stmt.where(Cp.id_ae == id)
        return self

    def do_all(self):
        """
        Effectue la recherche et retourne tous les résultats
        :return:
        """
        return db.session.execute(self._stmt).scalars()
