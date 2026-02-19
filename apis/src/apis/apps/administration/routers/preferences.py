"""Router FastAPI pour la gestion des préférences utilisateurs.

Ce module expose les endpoints suivants :
- POST /users/preferences : Créer une préférence
- GET /users/preferences : Lister les préférences de l'utilisateur
- GET /users/preferences/{uuid} : Récupérer une préférence spécifique
- POST /users/preferences/{uuid} : Mettre à jour une préférence
- DELETE /users/preferences/{uuid} : Supprimer une préférence
- GET /users/preferences/search-user : Rechercher des utilisateurs Keycloak
"""

import logging
from http import HTTPStatus

from fastapi import APIRouter, Depends, Request
from fastapi.params import Query
from prefect.deployments import arun_deployment
from sqlalchemy.orm import Session

from apis.apps.administration.models.preferences import (
    PreferenceCreateRequest,
    PreferenceResponse,
    PreferencesListResponse,
    PreferenceUpdateRequest,
    UserSearchResponse,
)
from apis.clients.keycloak_admin import KeycloakAdminError, get_keycloak_admin
from apis.database import get_session_settings
from apis.exception_handlers import error_responses
from apis.security.keycloak_token_validator import KeycloakTokenValidator
from apis.shared.models import APISuccess
from apis.shared.request_utils import get_origin_referrer
from models.connected_user import ConnectedUser
from models.exceptions import BadRequestError, ForbiddenError, ServerError
from services.preferences.preferences_service import (
    create_preference as service_create_preference,
    delete_preference as service_delete_preference,
    get_preference_by_uuid as service_get_preference_by_uuid,
    get_user_preferences as service_get_user_preferences,
    increment_usage as service_increment_usage,
    update_preference as service_update_preference,
)


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/users/preferences", tags=["Préférences utilisateur"])
keycloak_validator = KeycloakTokenValidator.get_application_instance()


###########################
# Search user
@router.get(
    "/search-user",
    summary="Rechercher des utilisateurs Keycloak",
    description="Recherche des utilisateurs par nom d'utilisateur ou email pour le partage de préférences",
    response_model=APISuccess[list[UserSearchResponse]],
    responses=error_responses(),
)
async def search_users(
    username: str = Query(..., min_length=4, description="Terme de recherche (minimum 4 caractères)"),
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
):
    """Recherche des utilisateurs Keycloak pour le partage de préférences."""
    try:
        assert len(username) >= 4, "Le terme de recherche doit contenir au moins 4 caractères"

        # Récupérer le client Keycloak Admin
        keycloak_admin = get_keycloak_admin()

        # Rechercher les utilisateurs
        query = {"briefRepresentation": True, "enabled": True, "search": username}
        users = keycloak_admin.get_users(query)

        # Convertir en modèles de réponse
        response_data = [UserSearchResponse(username=user["username"]) for user in users]

        return APISuccess(
            code=HTTPStatus.OK,
            message=f"{len(response_data)} utilisateur(s) trouvé(s)",
            data=response_data,
        )
    except KeycloakAdminError as e:
        logger.error("Erreur Keycloak lors de la recherche d'utilisateurs", exc_info=e)
        raise BadRequestError(api_message="Erreur lors de la recherche d'utilisateurs dans Keycloak")
    except Exception as e:
        logger.error("Erreur lors de la recherche d'utilisateurs", exc_info=e)
        raise ServerError(api_message="Erreur lors de la recherche d'utilisateurs")


###########################
# CRUD préférences
@router.post(
    "",
    summary="Créer une préférence utilisateur",
    description="Crée une nouvelle préférence pour l'utilisateur connecté avec possibilité de partage",
    response_model=APISuccess[PreferenceResponse],
    responses=error_responses(),
    status_code=HTTPStatus.CREATED,
)
async def create_preference(
    request: Request,
    data: PreferenceCreateRequest,
    session: Session = Depends(get_session_settings),
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
):
    """Crée une nouvelle préférence pour l'utilisateur connecté."""
    try:
        # Convertir les ShareRequest en dicts pour le service
        shares_data = [share.model_dump() for share in data.shares]

        # Créer la préférence
        with session.begin():
            preference = await service_create_preference(
                username=user.email,
                client_id=user.azp,
                name=data.name,
                filters=data.filters,
                options=data.options,
                shares_data=shares_data,
                session=session,
            )

            # Si des partages existent, déclencher le flow Prefect d'envoi d'emails
            if len(preference.shares) > 0:
                await alaunch_share_filter_flow(
                    preference_uuid=str(preference.uuid),
                    host_link=get_origin_referrer(request),
                )

        # Convertir en modèle Pydantic de réponse
        response_data = PreferenceResponse.model_validate(preference)

        return APISuccess(
            code=HTTPStatus.CREATED,
            message="Préférence créée avec succès",
            data=response_data,
        )
    except Exception as e:
        logger.error("Erreur lors de la création de la préférence", exc_info=e)
        raise ServerError(api_message="Erreur lors de la création de la préférence")


@router.get(
    "",
    summary="Lister les préférences de l'utilisateur",
    description="Récupère toutes les préférences créées par l'utilisateur et celles partagées avec lui",
    response_model=APISuccess[PreferencesListResponse],
    responses=error_responses(),
)
async def list_preferences(
    session: Session = Depends(get_session_settings),
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
):
    """Liste les préférences de l'utilisateur connecté."""
    try:
        created_prefs, shared_prefs = await service_get_user_preferences(
            username=user.email,
            client_id=user.azp,
            session=session,
        )

        # Convertir en modèles Pydantic
        created_response = [PreferenceResponse.model_validate(pref) for pref in created_prefs]
        shared_response = [PreferenceResponse.model_validate(pref) for pref in shared_prefs]

        response_data = PreferencesListResponse(
            create_by_user=created_response,
            shared_with_user=shared_response,
        )

        return APISuccess(
            code=HTTPStatus.OK,
            message="Liste des préférences récupérée avec succès",
            data=response_data,
        )
    except Exception as e:
        logger.error("Erreur lors de la récupération des préférences", exc_info=e)
        raise ServerError(api_message="Erreur lors de la récupération des préférences")


@router.get(
    "/{uuid}",
    summary="Récupérer une préférence par UUID",
    description="Récupère une préférence spécifique et incrémente son compteur d'utilisation",
    response_model=APISuccess[PreferenceResponse],
    responses=error_responses(),
)
async def get_preference(
    uuid: str,
    session: Session = Depends(get_session_settings),
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
):
    """Récupère une préférence par son UUID."""
    try:
        preference = await service_get_preference_by_uuid(
            uuid=uuid,
            client_id=user.azp,
            session=session,
        )

        if not preference:
            raise BadRequestError(api_message=f"Préférence {uuid} introuvable")

        # Incrémenter le compteur d'utilisation
        await service_increment_usage(preference, session)

        # Convertir en modèle Pydantic
        response_data = PreferenceResponse.model_validate(preference)

        return APISuccess(
            code=HTTPStatus.OK,
            message="Préférence récupérée avec succès",
            data=response_data,
        )
    except BadRequestError:
        raise
    except Exception as e:
        logger.error(f"Erreur lors de la récupération de la préférence {uuid}", exc_info=e)
        raise ServerError(api_message="Erreur lors de la récupération de la préférence")


@router.post(
    "/{uuid}",
    summary="Mettre à jour une préférence",
    description="Met à jour une préférence existante (nom, filtres, options, partages)",
    response_model=APISuccess[PreferenceResponse],
    responses=error_responses(),
)
async def update_preference(
    uuid: str,
    request: Request,
    data: PreferenceUpdateRequest,
    session: Session = Depends(get_session_settings),
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
):
    """Met à jour une préférence existante."""
    try:
        # Convertir les ShareRequest en dicts pour le service
        shares_data = [share.model_dump() for share in data.shares]

        with session.begin():
            # Mettre à jour la préférence
            preference = await service_update_preference(
                uuid=uuid,
                username=user.email,
                client_id=user.azp,
                name=data.name,
                filters=data.filters,
                options=data.options,
                shares_data=shares_data,
                session=session,
            )

            session.refresh(preference)  # Rafraîchir l'instance pour obtenir les partages mis à jour
            preference_response = PreferenceResponse.model_validate(preference)

            # Si des partages existent, déclencher le flow Prefect
            if len(preference.shares) > 0:
                await alaunch_share_filter_flow(
                    preference_uuid=str(preference.uuid),
                    host_link=get_origin_referrer(request),
                )

        return APISuccess(
            code=HTTPStatus.OK,
            message="Préférence mise à jour avec succès",
            data=preference_response,
        )
    except ValueError as e:
        if "droits" in str(e).lower():
            raise ForbiddenError()
        raise BadRequestError(api_message=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de la mise à jour de la préférence {uuid}", exc_info=e)
        raise ServerError(api_message="Erreur lors de la mise à jour de la préférence")


@router.delete(
    "/{uuid}",
    summary="Supprimer une préférence",
    description="Supprime définitivement une préférence",
    response_model=APISuccess[str],
    responses=error_responses(),
)
async def delete_preference(
    uuid: str,
    session: Session = Depends(get_session_settings),
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user()),
):
    """Supprime une préférence."""
    try:
        await service_delete_preference(
            uuid=uuid,
            username=user.email,
            client_id=user.azp,
            session=session,
        )

        return APISuccess(
            code=HTTPStatus.OK,
            message="Préférence supprimée avec succès",
            data="Success",
        )
    except ValueError as e:
        if "droits" in str(e).lower():
            raise ForbiddenError()
        raise BadRequestError(api_message=str(e))
    except Exception as e:
        logger.error(f"Erreur lors de la suppression de la préférence {uuid}", exc_info=e)
        raise ServerError(api_message="Erreur lors de la suppression de la préférence")


async def alaunch_share_filter_flow(preference_uuid: str, host_link: str):
    """Fonction utilitaire pour lancer le flow Prefect de partage de préférence."""
    run = await arun_deployment(
        name="share-filter-user/share_filter_user",
        parameters={
            "preference_uuid": preference_uuid,
            "host_link": host_link,
        },
        timeout=0,  # fire and forget
    )
    return run
