def sanitize_source_region_for_bdd_request(
    source_region: str | None,
    data_source: str | None = None,
) -> str | None:
    """Normalise la source region pour requête en bdd, supprime le leading '0' si besoin."""
    sanitized = source_region.lstrip("0") if source_region else None
    if sanitized is None and data_source != "NATION":
        raise ValueError("La region doit être renseignée.")
    return sanitized


def get_request_regions(sanitized_region: str) -> list[str]:
    # On autorise tout le monde a voir les données "Administration centrale" dont le code en base est "00"
    return ["00", sanitized_region]
