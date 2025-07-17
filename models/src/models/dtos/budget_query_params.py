

from typing import Literal

from models.dtos.colonne import Colonne


class BudgetQueryParams:
    # Params
    source_region: str | None = None
    data_source: str | None = None
    source: str | None = None
    n_ej: list[str] | None = None
    code_programme: list[str] | None = None
    niveau_geo: str | None = None
    code_geo: list[str] | None = None
    ref_qpv: int | None = None
    code_qpv: list[str] | None = None
    theme: list[str] | None = None
    siret_beneficiaire: list[str] | None = None
    types_beneficiaire: list[str] | None = None
    annee: Literal[2015, 2024] | None = None
    centres_couts: list[str] | None = None
    domaine_fonctionnel: list[str] | None = None
    referentiel_programmation: list[str] | None = None
    tags: list[str] | None = None
    # Colonnes
    colonnes: list[Colonne] | None = None
    # Grouping
    grouping: list[Colonne] | None = None
    grouped: list[str] | None = None
    # Pagination
    page: int = 1
    page_size: int = 100
    # Sorting
    sort_by: str | None = None
    sort_order: Literal["asc", "desc"] | None = None
    # Search
    search: str | None = None