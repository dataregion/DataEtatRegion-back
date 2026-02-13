"""Modèles Pydantic pour les préférences utilisateurs."""

from datetime import datetime
from typing import Any
from pydantic import BaseModel, EmailStr, ConfigDict, Field


class ShareRequest(BaseModel):
    """Modèle de requête pour le partage d'une préférence."""

    shared_username_email: EmailStr = Field(..., description="Email de l'utilisateur avec qui partager la préférence")


class PreferenceCreateRequest(BaseModel):
    """Modèle de requête pour la création d'une préférence."""

    name: str = Field(..., description="Nom de la préférence", min_length=1, max_length=255)
    filters: dict[str, Any] = Field(..., description="Critères de filtrage en format JSON")
    options: dict[str, Any] | None = Field(
        default=None, description="Options supplémentaires (colonnes, groupement, etc.)"
    )
    shares: list[ShareRequest] = Field(default_factory=list, description="Liste des utilisateurs avec qui partager")


class PreferenceUpdateRequest(BaseModel):
    """Modèle de requête pour la mise à jour d'une préférence."""

    name: str = Field(..., description="Nom de la préférence", min_length=1, max_length=255)
    filters: dict[str, Any] = Field(..., description="Critères de filtrage en format JSON")
    options: dict[str, Any] | None = Field(
        default=None, description="Options supplémentaires (colonnes, groupement, etc.)"
    )
    shares: list[ShareRequest] = Field(default_factory=list, description="Liste des utilisateurs avec qui partager")


class ShareResponse(BaseModel):
    """Modèle de réponse pour un partage de préférence."""

    model_config = ConfigDict(from_attributes=True)

    shared_username_email: str = Field(..., description="Email de l'utilisateur")
    email_send: bool = Field(default=False, description="Indique si l'email de notification a été envoyé")
    date_email_send: datetime | None = Field(default=None, description="Date d'envoi de l'email de notification")


class PreferenceResponse(BaseModel):
    """Modèle de réponse pour une préférence."""

    model_config = ConfigDict(from_attributes=True)

    uuid: str = Field(..., description="Identifiant unique de la préférence")
    username: str = Field(..., description="Nom d'utilisateur du créateur de la préférence")
    name: str = Field(..., description="Nom de la préférence")
    filters: dict[str, Any] = Field(..., description="Critères de filtrage en format JSON")
    options: dict[str, Any] | None = Field(
        default=None, description="Options supplémentaires (colonnes, groupement, etc.)"
    )
    shares: list[ShareResponse] = Field(default_factory=list, description="Liste des partages de cette préférence")
    nombre_utilisation: int = Field(default=0, description="Nombre de fois que la préférence a été utilisée")
    dernier_acces: datetime | None = Field(default=None, description="Date du dernier accès à la préférence")
    application_clientid: str = Field(..., description="Client ID de l'application")
    date_creation: datetime | None = Field(default=None, description="Date de création de la préférence")


class PreferencesListResponse(BaseModel):
    """Modèle de réponse pour la liste des préférences d'un utilisateur."""

    create_by_user: list[PreferenceResponse] = Field(
        default_factory=list, description="Préférences créées par l'utilisateur"
    )
    shared_with_user: list[PreferenceResponse] = Field(
        default_factory=list, description="Préférences partagées avec l'utilisateur"
    )


class UserSearchResponse(BaseModel):
    """Modèle de réponse pour la recherche d'utilisateurs Keycloak."""

    username: str = Field(..., description="Nom d'utilisateur Keycloak")
