from apis.apps.administration.models.preferences import UserSearchResponse
from apis.clients.keycloak_admin import get_keycloak_admin


def search_by_region(region: int, username: str | None = None) -> list[UserSearchResponse]:
    """
    Récupérer la liste des utilisateurs en fonction de leur région, via les groupes keycloak.

    Pour des questions de performance et pour éviter la gestion des doublons,
    on ne recherche que dans le groupe budget. Le groupe QPV est ignoré.

    Returns:
        list[UserSearchResponse]: La liste des utilisateurs trouvés.

    Raises:
        KeycloakAdminError: En cas d'erreur du client Keycloak.
    """
    keycloak_admin = get_keycloak_admin()

    # exclut tous les groupes spécialisés de type REGION.QPV ou autre
    groups = [group for group in keycloak_admin.get_groups({"q": f"region:{region}"}) if "." not in group["name"]]

    if len(groups) > 1:
        raise Exception(f"Plusieurs groupes pour la région {region}")

    users = keycloak_admin.get_group_members(
        groups[0]["id"],
        {
            "briefRepresentation": True,
            "enabled": True,
        },
    )

    # Convertir en modèles de réponse
    return [UserSearchResponse(username=user["username"]) for user in users if username in user.get("username")]
