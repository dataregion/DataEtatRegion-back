import dataclasses
import logging
import pandas

from sqlalchemy import delete
from app.database import db
from app.models.audit.AuditUpdateData import AuditUpdateData
from app.models.enums.DataType import DataType
from app.models.financial.France2030 import France2030
from app.models.refs.commune import Commune
from app.models.refs.nomenclature_france_2030 import NomenclatureFrance2030

from sqlalchemy.orm import contains_eager

from app.models.refs.siret import Siret
from app.services.file_service import check_file_and_save
from app.services.helper import TypeCodeGeoToFrance2030CodeGeoResolver
from app.servicesapp.exceptions.code_geo import NiveauCodeGeoException


@dataclasses.dataclass
class SousAxePlanRelancePayload:
    label: str
    axe: str


@dataclasses.dataclass
class StructurePayload:
    label: str
    siret: str


@dataclasses.dataclass
class TerritoirePayload:
    Commune: str
    CodeInsee: int


def _map_france_2030_row_laureats(france2030: France2030):
    """Mappe une ligne france 2030 en une ligne pour l'application laureats"""
    dict = {}

    if france2030 is not None:
        dict["Structure"] = france2030.nom_beneficiaire
        dict["Num\u00e9roDeSiretSiConnu"] = france2030.siret
        dict["SubventionAccord\u00e9e"] = france2030.montant_subvention

    if france2030 is not None and france2030.nomenclature is not None:
        dict["axe"] = f"{france2030.nomenclature.code} - {france2030.nomenclature.mot}"

    return dict


def _map_france_2030_row_structure(france2030: France2030) -> StructurePayload | None:
    """Mappe un bénéficiaire france 2030 avec une structure france relance"""
    if france2030.beneficiaire is None:
        return None

    benef: Siret = france2030.beneficiaire
    return StructurePayload(label=benef.denomination, siret=benef.code)  # type: ignore


def liste_axes_france2030() -> list[SousAxePlanRelancePayload]:
    """
    Liste les axes - correspondant aux objectifs
    de france 2030
    """
    stmt = db.select(NomenclatureFrance2030)
    result = db.session.execute(stmt)
    nomenclatures = result.fetchall()

    payload = [SousAxePlanRelancePayload(axe=x[0].code, label=x[0].mot) for x in nomenclatures]
    return payload


def search_france_2030_beneficiaire(term: str, limit=10):
    """Recherche les bénéficiaires par nom"""
    stmt = db.select(France2030).join(Siret).options(contains_eager(France2030.beneficiaire))

    if term is not None and len(term) > 0:
        stmt = stmt.where(Siret.denomination.ilike(f"%{term}%"))

    stmt = stmt.limit(limit)

    result = db.session.execute(stmt).fetchall()

    mapped = [_map_france_2030_row_structure(x[0]) for x in result]  # type: ignore
    payload = list(filter(None, mapped))
    return payload


def search_france_2030(
    axes: list[str] | None = None,
    structures: list[str] | None = None,
    niveau_geo: str | None = None,
    code_geo: list | None = None,
    page_number=1,
    limit=500,
    **kwargs,
):
    stmt = (
        db.select(France2030)
        .outerjoin(NomenclatureFrance2030)
        .options(contains_eager(France2030.nomenclature))
        .outerjoin(Siret)
        .options(contains_eager(France2030.beneficiaire))
        .outerjoin(Commune)
    )

    if axes is not None:
        stmt = stmt.where(NomenclatureFrance2030.mot.in_(axes))

    if structures is not None:
        stmt = stmt.where(Siret.denomination.in_(structures))

    if niveau_geo is not None and code_geo is not None:
        code_geo_column = TypeCodeGeoToFrance2030CodeGeoResolver().code_geo_column(niveau_geo)
        stmt = stmt.where(code_geo_column.in_(code_geo))
    elif bool(niveau_geo) ^ bool(code_geo):
        raise NiveauCodeGeoException("Les paramètres niveau_geo et code_geo doivent être fournis ensemble.")

    # paginate
    page_result = db.paginate(stmt, per_page=limit, page=page_number, error_out=False)
    page_result.items = [_map_france_2030_row_laureats(x) for x in page_result.items]
    return page_result


def _check_france_2030_filestructure(file_france):
    header_only = pandas.read_csv(file_france, nrows=0)
    headers = header_only.columns.tolist()

    if France2030.get_columns_files() != headers:
        raise Exception("Header incorrects pour le fichier de france 2030")


def _delete_france_2030(annee: int):
    """Supprime les lignes de france 2030 pour une année donnée."""

    logging.info(f"[IMPORT FRANCE 2030] Suppression des lignes pour l'année {annee}")
    stmt = delete(France2030).where(France2030.annee == annee)
    db.session.execute(stmt)
    db.session.commit()


def import_france_2030(file_france, annee: int, username=""):
    save_path = check_file_and_save(file_france)

    logging.info(f"[IMPORT FRANCE 2030] Récupération du fichier {save_path}")

    _delete_france_2030(annee)
    from app.tasks.financial.import_france_2030 import import_file_france_2030

    _check_france_2030_filestructure(str(save_path))
    task = import_file_france_2030.delay(str(save_path), annee=annee)
    db.session.add(AuditUpdateData(username=username, filename=file_france.filename, data_type=DataType.FRANCE_2030))
    db.session.commit()
    return task
