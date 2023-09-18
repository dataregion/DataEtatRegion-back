import logging
import pandas
from sqlalchemy import delete

from sqlalchemy.orm import contains_eager, selectinload
import json

from app import db
from app.exceptions.exceptions import InvalidFile, FileNotAllowedException
from app.models.audit.AuditUpdateData import AuditUpdateData
from app.models.enums.DataType import DataType
from app.models.financial.Ademe import Ademe

from app.models.financial.FinancialCp import FinancialCp
from app.models.financial.FinancialAe import FinancialAe
from app.models.refs.categorie_juridique import CategorieJuridique
from app.models.refs.commune import Commune
from app.models.refs.domaine_fonctionnel import DomaineFonctionnel
from app.models.refs.referentiel_programmation import ReferentielProgrammation
from app.models.refs.siret import Siret
from app.models.tags.Tags import Tags
from app.services import BuilderStatementFinancial
from app.services import BuilderStatementFinancialCp
from app.services.code_geo import BuilderCodeGeo
from app.services.file_service import check_file_and_save


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
        force_update=force_update,
    )
    db.session.add(AuditUpdateData(username=username, filename=file_ae.filename, data_type=DataType.FINANCIAL_DATA_AE))
    db.session.commit()
    return task


def import_cp(file_cp, source_region: str, annee: int, username=""):
    save_path = check_file_and_save(file_cp)

    _check_file(save_path, FinancialCp.get_columns_files_cp())
    source_region = _sanitize_source_region(source_region)

    logging.info(f"[IMPORT FINANCIAL] Récupération du fichier {save_path}")
    csv_options = {
        "sep": ",",
        "skiprows": 8,
    }

    _delete_cp(annee, source_region)
    from app.tasks.files.file_task import split_csv_files_and_run_task

    task = split_csv_files_and_run_task.delay(
        str(save_path), "import_file_cp_financial", json.dumps(csv_options), source_region=source_region, annee=annee
    )

    db.session.add(AuditUpdateData(username=username, filename=file_cp.filename, data_type=DataType.FINANCIAL_DATA_CP))
    db.session.commit()
    return task


def import_france_2030(file_france, username=""):
    save_path = check_file_and_save(file_france, allowed_extensions={"xlsx"})

    logging.info(f"[IMPORT FRANCE 2030] Récupération du fichier {save_path}")
    from app.tasks.financial.import_france_2030 import import_file_france_2030

    task = import_file_france_2030.delay(str(save_path))
    db.session.add(AuditUpdateData(username=username, filename=file_france.filename, data_type=DataType.FRANCE_2030))
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
    code_geo: list = None,
    annee: list = None,
    tags: list[str] = None,
    page_number=1,
    limit=500,
):
    query = db.select(Ademe).options(
        contains_eager(Ademe.ref_siret_beneficiaire)
        .load_only(Siret.code, Siret.denomination)
        .contains_eager(Siret.ref_commune)
        .load_only(Commune.label_commune, Commune.code),
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

    # utilisation du builder
    query_ademe = BuilderStatementFinancial(query)

    if code_geo is not None:
        (type_geo, list_code_geo) = BuilderCodeGeo().build_list_code_geo(code_geo)
        query_ademe.where_geo(type_geo, list_code_geo)
    else:
        query_ademe.join_commune()

    if annee is not None:
        query_ademe.where_custom(db.func.extract("year", Ademe.date_convention).in_(annee))

    if tags is not None:
        _tags = map(_sanitize_tag_fullname_for_db, tags)
        fullnamein = Tags.fullname.in_(_tags)
        query_ademe.where_custom(Ademe.tags.any(fullnamein))

    page_result = query_ademe.do_paginate(limit, page_number)
    return page_result


def get_ademe(id: int) -> Ademe:
    query = db.select(Ademe).join(Siret, Ademe.ref_siret_beneficiaire).join(Siret.ref_categorie_juridique)

    result = BuilderStatementFinancial(query).join_commune().where_custom(Ademe.id == id).do_single()
    return result


def search_financial_data_ae(
    code_programme: list = None,
    theme: list = None,
    siret_beneficiaire: list = None,
    annee: list = None,
    domaine_fonctionnel: list = None,
    referentiel_programmation: list = None,
    source_region: str = None,
    code_geo: list = None,
    tags: list[str] = None,
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

    if code_geo is not None:
        (type_geo, list_code_geo) = BuilderCodeGeo().build_list_code_geo(code_geo)
        query_ae.where_geo_ae(type_geo, list_code_geo, source_region)
    else:
        query_ae.join_commune().join_localisation_interministerielle()

    if domaine_fonctionnel is not None:
        query_ae.where_custom(DomaineFonctionnel.code.in_(domaine_fonctionnel))

    if referentiel_programmation is not None:
        query_ae.where_custom(ReferentielProgrammation.code.in_(referentiel_programmation))

    if source_region is not None:
        query_ae.where_custom(FinancialAe.source_region == source_region)

    if tags is not None:
        _tags = map(_sanitize_tag_fullname_for_db, tags)
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
    return source_region.lstrip("0")


def _sanitize_tag_fullname_for_db(tag: str):
    """Convertit les noms de tags reçu de l'API en fullname"""
    if not ":" in tag:
        return tag + ":"
    return tag


def _delete_cp(annee: int, source_region: str):
    """
    Supprimes CP d'une année comptable
    :param annee:
    :param source_region:
    :return:
    """
    stmt = delete(FinancialCp).where(FinancialCp.annee == annee).where(FinancialCp.source_region == source_region)
    db.session.execute(stmt)
    db.session.commit()
