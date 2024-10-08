import json
import logging
import pandas
from sqlalchemy import or_

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
from app.models.refs.domaine_fonctionnel import DomaineFonctionnel
from app.models.refs.referentiel_programmation import ReferentielProgrammation
from app.models.refs.siret import Siret
from app.models.tags.Tags import Tags
from app.services import BuilderStatementFinancial
from app.services import BuilderStatementFinancialCp
from app.models.tags.Tags import TagVO
from app.services.data import BuilderStatementFinancialLine
from app.servicesapp.exceptions.code_geo import NiveauCodeGeoException
from app.services.file_service import check_file_and_save
from app.services.financial_data import delete_cp_annee_region


def import_financial_data(file_ae: str, file_cp: str, source_region: str, annee: int, username=""):
    # Sanitize des paramètres
    source_region = _sanitize_source_region(source_region)
    # Validation des fichiers
    save_path_ae = check_file_and_save(file_ae)
    save_path_cp = check_file_and_save(file_cp)
    _check_file(save_path_ae, FinancialAe.get_columns_files_ae())
    _check_file(save_path_cp, FinancialCp.get_columns_files_cp())

    # Enregistrement de l'import à effectuer
    db.session.add(
        AuditInsertFinancialTasks(
            fichier_ae=save_path_ae,
            fichier_cp=save_path_cp,
            source_region=source_region,
            annee=annee,
            username=username,
        )
    )
    db.session.commit()


# TODO : deprecated
def import_ae(file_ae, source_region: str, annee: int, force_update: bool, username=""):
    save_path = check_file_and_save(file_ae)

    _check_file(save_path, FinancialAe.get_columns_files_ae())
    source_region = _sanitize_source_region(source_region)

    logging.info(f"[IMPORT FINANCIAL] Récupération du fichier {save_path}")
    csv_options = {"sep": ",", "skiprows": 8}
    from app.tasks.files.file_task import split_csv_files_and_run_task

    task = split_csv_files_and_run_task.delay(
        str(save_path),
        "import_file_ae_financial",
        json.dumps(csv_options),
        source_region=source_region,
        annee=annee,
    )
    db.session.add(AuditUpdateData(username=username, filename=file_ae.filename, data_type=DataType.FINANCIAL_DATA_AE))
    db.session.commit()
    return task


# TODO : deprecated
def import_cp(file_cp, source_region: str, annee: int, username=""):
    save_path = check_file_and_save(file_cp)

    _check_file(save_path, FinancialCp.get_columns_files_cp())
    source_region = _sanitize_source_region(source_region)

    logging.info(f"[IMPORT FINANCIAL] Récupération du fichier {save_path}")
    csv_options = {
        "sep": ",",
        "skiprows": 8,
    }

    delete_cp_annee_region(annee, source_region)
    from app.tasks.files.file_task import split_csv_files_and_run_task

    task = split_csv_files_and_run_task.delay(
        str(save_path), "import_file_cp_financial", json.dumps(csv_options), source_region=source_region, annee=annee
    )

    db.session.add(AuditUpdateData(username=username, filename=file_cp.filename, data_type=DataType.FINANCIAL_DATA_CP))
    db.session.commit()
    return task


def import_ademe(file_ademe, username=""):
    save_path = check_file_and_save(file_ademe)

    logging.info(f"[IMPORT ADEME] Récupération du fichier {save_path}")
    from app.tasks.financial.import_financial import import_file_ademe

    task = import_file_ademe.delay(str(save_path))
    db.session.add(AuditUpdateData(username=username, filename=file_ademe.filename, data_type=DataType.ADEME))
    db.session.commit()
    return task


def get_financial_ae(id: int) -> FinancialAe:
    query_select = (
        BuilderStatementFinancial()
        .select_ae()
        .join_filter_siret()
        .join_filter_programme_theme()
        .join_commune()
        .join_localisation_interministerielle()
        .by_ae_id(id)
        .options_select_load()
    )

    result = query_select.do_single()
    return result


def get_financial_cp_of_ae(id: int):
    return BuilderStatementFinancialCp().select_cp().by_ae_id(id).order_by_date().do_all()


def get_annees_ae():
    return db.session.execute(
        db.text("SELECT ARRAY(SELECT DISTINCT annee FROM public.financial_ae)")
    ).scalar_one_or_none()


def search_ademe(
    siret_beneficiaire: list = None,
    niveau_geo: str = None,
    code_geo: list = None,
    annee: list = None,
    tags: list[str] = None,
    page_number=1,
    limit=500,
):
    query = db.select(Ademe).options(
        contains_eager(Ademe.ref_siret_beneficiaire)
        .load_only(Siret.code, Siret.denomination)
        .contains_eager(Siret.ref_commune),
        contains_eager(Ademe.ref_siret_beneficiaire)
        .contains_eager(Siret.ref_categorie_juridique)
        .load_only(CategorieJuridique.type),
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


def get_ademe(id: int) -> Ademe:
    query = db.select(Ademe).join(Siret, Ademe.ref_siret_beneficiaire).join(Siret.ref_categorie_juridique)

    result = BuilderStatementFinancial(query).join_commune().where_custom(Ademe.id == id).do_single()
    return result


def search_financial_data_ae(
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
    tags: list[str] | None = None,
    page_number=1,
    limit=500,
):
    source_region = _sanitize_source_region(source_region)

    query_ae = (
        BuilderStatementFinancial()
        .select_ae()
        .join_filter_siret(siret_beneficiaire)
        .join_filter_programme_theme(code_programme, theme)
    )

    if niveau_geo is not None and code_geo is not None:
        query_ae.where_geo_ae(TypeCodeGeo[niveau_geo.upper()], code_geo, source_region)
    elif bool(niveau_geo) ^ bool(code_geo):
        raise NiveauCodeGeoException("Les paramètres niveau_geo et code_geo doivent être fournis ensemble.")
    else:
        query_ae.join_commune().join_localisation_interministerielle()

    if domaine_fonctionnel is not None:
        query_ae.where_custom(DomaineFonctionnel.code.in_(domaine_fonctionnel))

    if referentiel_programmation is not None:
        query_ae.where_custom(ReferentielProgrammation.code.in_(referentiel_programmation))

    if source_region is not None:
        query_ae.where_custom(FinancialAe.source_region == source_region)

    type_beneficiaires_conditions = []
    if types_beneficiaires is not None:
        type_beneficiaires_conditions.append(CategorieJuridique.type.in_(types_beneficiaires))
    if types_beneficiaires is not None and "autres" in types_beneficiaires:
        type_beneficiaires_conditions.append(CategorieJuridique.type == None)  # noqa: E711

    query_ae.where_custom(or_(*type_beneficiaires_conditions))

    if tags is not None:
        _tags = map(TagVO.sanitize_str, tags)
        fullnamein = Tags.fullname.in_(_tags)
        query_ae.where_custom(FinancialAe.tags.any(fullnamein))

    page_result = query_ae.where_annee(annee).options_select_load().do_paginate(limit, page_number)
    return page_result


def _check_file(fichier, columns_name):
    try:
        check_column = pandas.read_csv(fichier, sep=",", skiprows=8, nrows=5)
    except Exception:
        logging.exception(msg="[CHECK FILE] Erreur de lecture du fichier")
        raise FileNotAllowedException(message="Erreur de lecture du fichier")

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
    return source_region.lstrip("0") if source_region else None


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
    tags: list[str] | None = None,
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
    )

    if niveau_geo is not None and code_geo is not None:
        query_lignes_budget.where_geo(TypeCodeGeo[niveau_geo.upper()], code_geo, source_region)
    elif bool(niveau_geo) ^ bool(code_geo):
        raise NiveauCodeGeoException("Les paramètres niveau_geo et code_geo doivent être fournis ensemble.")

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
