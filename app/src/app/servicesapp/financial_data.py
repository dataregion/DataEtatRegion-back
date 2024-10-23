import logging
import pandas

from sqlalchemy.orm import contains_eager, selectinload

from app import db
from app.exceptions.exceptions import InvalidFile, FileNotAllowedException
from app.models.audit.AuditInsertFinancialTasks import AuditInsertFinancialTasks
from app.models.audit.AuditUpdateData import AuditUpdateData
from app.models.enums.DataType import DataType
from app.models.enums.TypeCodeGeo import TypeCodeGeo
from app.models.financial.Ademe import Ademe

from app.models.financial.FinancialCp import FinancialCp
from app.models.financial.FinancialAe import FinancialAe
from app.models.refs.categorie_juridique import CategorieJuridique
from app.models.refs.siret import Siret
from app.models.tags.Tags import Tags
from app.services import BuilderStatementFinancial, FileStorageProtocol
from app.services import BuilderStatementFinancialCp
from app.models.tags.Tags import TagVO
from app.services.data import BuilderStatementFinancialLine
from app.servicesapp.exceptions.authentication import NoCurrentRegion
from app.servicesapp.exceptions.code_geo import NiveauCodeGeoException
from app.services.file_service import check_file_and_save


def import_financial_data(
    file_ae: FileStorageProtocol, file_cp: FileStorageProtocol, source_region: str, annee: int, username=""
):
    # Sanitize des paramètres
    _source_region = _sanitize_source_region(source_region)
    # Validation des fichiers
    save_path_ae = check_file_and_save(file_ae)
    save_path_cp = check_file_and_save(file_cp)
    _check_file(save_path_ae, FinancialAe.get_columns_files_ae())
    _check_file(save_path_cp, FinancialCp.get_columns_files_cp())

    # Enregistrement de l'import à effectuer
    db.session.add(
        AuditInsertFinancialTasks(
            fichier_ae=save_path_ae,  # type: ignore
            fichier_cp=save_path_cp,  # type: ignore
            source_region=_source_region,  # type: ignore
            annee=annee,  # type: ignore
            username=username,  # type: ignore
        )
    )
    db.session.commit()


def import_ademe(file_ademe, username=""):
    save_path = check_file_and_save(file_ademe)

    logging.info(f"[IMPORT ADEME] Récupération du fichier {save_path}")
    from app.tasks.financial.import_financial import import_file_ademe

    task = import_file_ademe.delay(str(save_path))
    db.session.add(AuditUpdateData(username=username, filename=file_ademe.filename, data_type=DataType.ADEME))  # type: ignore
    db.session.commit()
    return task


def get_financial_cp_of_ae(id: int):
    return BuilderStatementFinancialCp().select_cp().by_ae_id(id).order_by_date().do_all()


def search_ademe(
    siret_beneficiaire: list | None = None,
    niveau_geo: str | None = None,
    code_geo: list | None = None,
    annee: list | None = None,
    tags: list[str] | None = None,
    page_number=1,
    limit=500,
):
    query = db.select(Ademe).options(
        contains_eager(Ademe.ref_siret_beneficiaire)
        .load_only(Siret.code, Siret.denomination)  # type: ignore
        .contains_eager(Siret.ref_commune),
        contains_eager(Ademe.ref_siret_beneficiaire)
        .contains_eager(Siret.ref_categorie_juridique)
        .load_only(CategorieJuridique.type),  # type: ignore
        selectinload(Ademe.tags),
    )
    query = (
        query.join(Ademe.ref_siret_beneficiaire.and_(Siret.code.in_(siret_beneficiaire)))
        if siret_beneficiaire is not None
        else query.join(Siret, Ademe.ref_siret_beneficiaire)
    )
    query = query.join(Siret.ref_categorie_juridique)
    query = query.join(Siret.ref_qpv, isouter=True)

    # utilisation du builder
    query_ademe = BuilderStatementFinancial(query)

    if niveau_geo is not None and code_geo is not None:
        query_ademe.where_geo(TypeCodeGeo[niveau_geo.upper()], code_geo)
    elif bool(niveau_geo) ^ bool(code_geo):
        raise NiveauCodeGeoException("Les paramètres niveau_geo et code_geo doivent être fournis ensemble.")
    else:
        query_ademe.join_commune()

    if annee is not None:
        query_ademe.where_custom(db.func.extract("year", Ademe.date_convention).in_(annee))

    if tags is not None:
        _tags = map(TagVO.sanitize_str, tags)
        fullnamein = Tags.fullname.in_(_tags)
        query_ademe.where_custom(Ademe.tags.any(fullnamein))

    page_result = query_ademe.do_paginate(limit, page_number)
    return page_result


def get_ademe(id: int) -> Ademe | None:
    query = db.select(Ademe).join(Siret, Ademe.ref_siret_beneficiaire).join(Siret.ref_categorie_juridique)

    result = BuilderStatementFinancial(query).join_commune().where_custom(Ademe.id == id).do_single()
    return result


def _check_file(fichier: str, columns_name):
    try:
        check_column = pandas.read_csv(fichier, sep=",", skiprows=8, nrows=5)
    except Exception as _:
        logging.exception(msg="[CHECK FILE] Erreur de lecture du fichier")
        raise InvalidFile()

    # check nb colonnes
    if len(check_column.columns) != len(columns_name):
        raise InvalidFile(message="Le fichier n'a pas les bonnes colonnes")

    try:
        data_financial = pandas.read_csv(
            fichier,
            sep=",",
            skiprows=8,
            nrows=5,
            names=columns_name,
            dtype={"n_ej": str, "n_poste_ej": str, "fournisseur_titulaire": str, "siret": str},
        )
    except Exception:
        logging.exception(msg="[CHECK FILE] Erreur de lecture du fichier")
        raise FileNotAllowedException(message="Erreur de lecture du fichier")

    if data_financial.isnull().values.any():
        raise InvalidFile(message="Le fichier contient des valeurs vides")


def _sanitize_source_region(source_region):
    sanitized = source_region.lstrip("0") if source_region else None
    if sanitized is None:
        raise NoCurrentRegion()
    return sanitized


def get_ligne_budgetaire(
    source: DataType,
    id: int,
    source_region: str | None = None,
):
    """
    Recherche la ligne budgetaire selon son ID et sa source region
    """
    source_region = _sanitize_source_region(source_region)

    query_ligne_budget = (
        BuilderStatementFinancialLine().par_identifiant_technique(source, id).source_region_in([source_region])
    )
    result = query_ligne_budget.do_single()
    return result


def search_lignes_budgetaires(
    n_ej: list | None = None,
    source: str | None = None,
    code_programme: list | None = None,
    theme: list | None = None,
    siret_beneficiaire: list | None = None,
    types_beneficiaires: list | None = None,
    annee: list | None = None,
    domaine_fonctionnel: list | None = None,
    referentiel_programmation: list | None = None,
    source_region: str | None = None,
    niveau_geo: str | None = None,
    code_geo: list | None = None,
    ref_qpv: int | None = None,
    code_qpv: list | None = None,
    tags: list[str] | None = None,
    data_source: str | None = None,
    page_number=1,
    limit=500,
):
    """
    Recherche les lignes budgetaires (quelle que soit la source)
    correspondant aux critères de recherche utilisateur.
    """

    source_region = _sanitize_source_region(source_region)

    query_lignes_budget = (
        BuilderStatementFinancialLine()
        .beneficiaire_siret_in(siret_beneficiaire)
        .code_programme_in(code_programme)
        .themes_in(theme)
        .annee_in(annee)
        .domaine_fonctionnel_in(domaine_fonctionnel)
        .referentiel_programmation_in(referentiel_programmation)
        .source_region_in([source_region])
        .n_ej_in(n_ej)
        .source_is(source)
        .data_source_is(data_source)
    )

    if niveau_geo is not None and code_geo is not None:
        query_lignes_budget.where_geo(TypeCodeGeo[niveau_geo.upper()], code_geo, source_region)
    elif bool(niveau_geo) ^ bool(code_geo):
        raise NiveauCodeGeoException("Les paramètres niveau_geo et code_geo doivent être fournis ensemble.")

    if ref_qpv is not None and code_qpv is not None:
        if ref_qpv != 2015 and ref_qpv != 2024:
            raise NiveauCodeGeoException("Mauvaise année de découpage QPV.")
        query_lignes_budget.where_geo(
            TypeCodeGeo.QPV if ref_qpv == 2015 else TypeCodeGeo.QPV24, code_qpv, source_region
        )
    elif bool(ref_qpv) ^ bool(code_qpv):
        raise NiveauCodeGeoException("Les paramètres ref_qpv et codes_qpv doivent être fournis ensemble.")

    _includes_nones = False
    if types_beneficiaires is not None and "autres" in types_beneficiaires:
        _includes_nones = True
    query_lignes_budget.type_categorie_juridique_du_beneficiaire_in(types_beneficiaires, includes_none=_includes_nones)

    query_lignes_budget.tags_fullname_in(tags)

    page_result = query_lignes_budget.do_paginate(limit, page_number)
    return page_result


def get_annees_budget(source_region: str | None = None):
    source_region = _sanitize_source_region(source_region)

    query_annees_budget = BuilderStatementFinancialLine().source_region_in([source_region])
    return query_annees_budget.do_select_annees()
