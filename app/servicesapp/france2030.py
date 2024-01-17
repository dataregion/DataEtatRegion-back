import dataclasses
from app.database import db
from app.models.financial.France2030 import France2030
from app.models.refs.nomenclature_france_2030 import NomenclatureFrance2030

from sqlalchemy.orm import contains_eager

from app.models.refs.siret import Siret


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
    territoires: list[str] | None = None,
    page_number=1,
    limit=500,
    **kwargs,
):
    filtered = False
    stmt = (
        db.select(France2030)
        .join(NomenclatureFrance2030)
        .options(contains_eager(France2030.nomenclature))
        .join(Siret)
        .options(contains_eager(France2030.beneficiaire))
    )

    if axes is not None:
        stmt = stmt.where(NomenclatureFrance2030.mot.in_(axes))
        filtered = True

    if structures is not None:
        stmt = stmt.where(Siret.denomination.in_(structures))
        filtered = True

    if not filtered and territoires is not None and len(territoires) > 0:
        raise NotImplementedError("Filtrer les données uniquement par territoires n'est pas supporté.")

    # paginate
    page_result = db.paginate(stmt, per_page=limit, page=page_number, error_out=False)
    page_result.items = [_map_france_2030_row_laureats(x) for x in page_result.items]
    return page_result
