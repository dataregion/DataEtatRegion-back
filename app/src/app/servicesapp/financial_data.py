import logging
import pandas

from sqlalchemy.orm import contains_eager, selectinload

from app import db
from app.exceptions.exceptions import InvalidFile, FileNotAllowedException
from models.entities.audit.AuditInsertFinancialTasks import AuditInsertFinancialTasks
from models.entities.audit.AuditUpdateData import AuditUpdateData
from models.value_objects.common import DataType
from models.value_objects.common import TypeCodeGeo
from models.entities.financial.Ademe import Ademe

from models.entities.financial.FinancialCp import FinancialCp
from models.entities.financial.FinancialAe import FinancialAe
from models.entities.refs.CategorieJuridique import CategorieJuridique
from models.entities.refs.Siret import Siret
from models.entities.common.Tags import Tags
from models.entities.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLines as FinancialLines

from app.services import BuilderStatementFinancial, FileStorageProtocol
from app.services import BuilderStatementFinancialCp
from models.value_objects.tags import TagVO
from services.financial_data import BuilderStatementFinancialLine
from app.servicesapp.exceptions.authentication import NoCurrentRegion
from app.servicesapp.exceptions.code_geo import NiveauCodeGeoException
from app.services.file_service import check_file_and_save

from app.utilities.observability import gauge_of_currently_executing, summary_of_time


def import_financial_data(
    file_ae: FileStorageProtocol,
    file_cp: FileStorageProtocol,
    source_region: str,
    annee: int,
    username="",
    client_id=None,
):
    # Sanitize des paramètres
    _source_region = _sanitize_source_region(source_region, "REGION")
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
            application_clientid=client_id,  # type: ignore
        )
    )
    db.session.commit()
    logging.info(f"[IMPORT REGION] AJout d'un import REGIONAL de {annee} pour {client_id}")


def import_national_data(
    file_ae: FileStorageProtocol, file_cp: FileStorageProtocol, annee: int, username="", client_id=None
):
    """
    Pour l'import national, ajout dans la table Audit Insert avec source_region = "NATIONAL" et annee =0
    """
    # Validation des fichiers
    save_path_ae = check_file_and_save(file_ae)
    save_path_cp = check_file_and_save(file_cp)
    db.session.add(
        AuditInsertFinancialTasks(
            fichier_ae=save_path_ae,  # type: ignore
            fichier_cp=save_path_cp,  # type: ignore
            source_region="NATIONAL",  # type: ignore
            annee=annee,
            username=username,  # type: ignore
            application_clientid=client_id,  # type: ignore
        )
    )
    db.session.commit()
    logging.info("[IMPORT NATION] AJout d'un import NATIONAL pour l'annee {annee} via client {client_id}")


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
    query = query.join(Siret.ref_qpv15, isouter=True)

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


def _sanitize_source_region(source_region: str, data_source: str) -> str | None:
    """Normalise la source region pour requête en bdd, supprime le leading '0' si besoin."""
    sanitized = source_region.lstrip("0") if source_region else None
    if sanitized is None and data_source != "NATION":
        raise NoCurrentRegion()
    return sanitized


def _get_request_regions(sanitized_region: str) -> list[str]:
    # On autorise tout le monde a voir les données "Administration centrale" dont le code en base est "00"
    return ["00", sanitized_region]


def get_ligne_budgetaire(source: DataType, id: int, source_region: str | None = None, data_source: str | None = None):
    """
    Recherche la ligne budgetaire selon son ID et sa source region
    """
    _session = db.session()
    source_region = _sanitize_source_region(source_region, data_source)
    _regions = _get_request_regions(source_region)

    query_ligne_budget = (
        BuilderStatementFinancialLine(_session).par_identifiant_technique(source, id).data_source_is(data_source)
    )
    if source_region is not None:
        query_ligne_budget = query_ligne_budget.source_region_in(_regions)

    result = query_ligne_budget.do_single()
    return result


@gauge_of_currently_executing()
@summary_of_time()
def search_lignes_budgetaires(
    n_ej: list | None = None,
    source: str | None = None,
    code_programme: list | None = None,
    theme: list | None = None,
    siret_beneficiaire: list | None = None,
    types_beneficiaires: list | None = None,
    annee: list | None = None,
    centres_couts: list | None = None,
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

    source_region = _sanitize_source_region(source_region, data_source)
    _regions = _get_request_regions(source_region)
    
    _session = db.session()

    query_lignes_budget = (
        BuilderStatementFinancialLine(_session)
        .beneficiaire_siret_in(siret_beneficiaire)
        .code_programme_in(code_programme)
        .themes_in(theme)
        .annee_in(annee)
        .centres_couts_in(centres_couts)
        .domaine_fonctionnel_in(domaine_fonctionnel)
        .referentiel_programmation_in(referentiel_programmation)
        .n_ej_in(n_ej)
        .source_is(source)
        .data_source_is(data_source)
    )
    if source_region is not None:
        query_lignes_budget = query_lignes_budget.source_region_in(_regions)

    if niveau_geo is not None and code_geo is not None:  # On recherche sur le beneficaire
        query_lignes_budget.where_geo(TypeCodeGeo[niveau_geo.upper()], code_geo, source_region)
    elif bool(niveau_geo) ^ bool(code_geo):
        raise NiveauCodeGeoException("Les paramètres niveau_geo et code_geo doivent être fournis ensemble.")

    if ref_qpv is not None:  ## special Data QPV. On recherche sur le
        if ref_qpv != 2015 and ref_qpv != 2024:
            raise NiveauCodeGeoException("Mauvaise année de découpage QPV.")
        if code_qpv is not None:
            query_lignes_budget.where_geo_loc_qpv(
                TypeCodeGeo.QPV if ref_qpv == 2015 else TypeCodeGeo.QPV24, code_qpv, source_region
            )
        # query_lignes_budget.where_geo(
        #     TypeCodeGeo.QPV if ref_qpv == 2015 else TypeCodeGeo.QPV24, code_qpv, source_region
        # )
        else:
            query_lignes_budget.where_qpv_not_null(FinancialLines.lieu_action_code_qpv)

    _includes_nones = False
    if types_beneficiaires is not None and "autres" in types_beneficiaires:
        _includes_nones = True
    query_lignes_budget.type_categorie_juridique_du_beneficiaire_in(types_beneficiaires, includes_none=_includes_nones)

    query_lignes_budget.tags_fullname_in(tags)

    page_incremental_result = query_lignes_budget.do_paginate_incremental(limit, page_number * limit)
    return page_incremental_result


def get_annees_budget(source_region: str | None = None, data_source: str | None = None):
    source_region = _sanitize_source_region(source_region, data_source)
    _regions = _get_request_regions(source_region)
    
    _session = db.session()

    if source_region is None:
        return BuilderStatementFinancialLine(_session).do_select_annees(None, data_source)
    return BuilderStatementFinancialLine(_session).do_select_annees(_regions, data_source)


def import_qpv_lieu_action(file_qpv, username=""):
    save_path = check_file_and_save(file_qpv)

    logging.info(f"[IMPORT][QPV_LIEU_ACTION] Récupération du fichier {save_path}")
    from app.tasks.financial.import_financial import import_file_qpv_lieu_action

    task = import_file_qpv_lieu_action.delay(str(save_path))
    return task
