"""Value objects pour l'API d'export des données."""

from typing import Literal


ExportTarget = Literal["csv", "xlsx", "ods", "to-grist"]
"""Format d'export des données. Cela peut être un format de fichier ou une cible plus abstraite."""


def is_file_format(format: ExportTarget) -> bool:
    """Indique si le format d'export est un format de fichier."""
    return format in ["csv", "xlsx", "ods"]
