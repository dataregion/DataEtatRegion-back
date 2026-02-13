"""Service de gestion des préférences utilisateurs.

Ce service contient toute la logique métier pour :
- Créer, lire, mettre à jour et supprimer des préférences
- Gérer les partages de préférences entre utilisateurs
- Incrémenter les compteurs d'utilisation
"""

import datetime
import logging
from typing import Any

import sqlalchemy
from sqlalchemy import cast
from sqlalchemy.orm import Session, lazyload

from models.entities.preferences.Preference import Preference, Share


logger = logging.getLogger(__name__)


async def get_user_preferences(
    username: str, client_id: str, session: Session
) -> tuple[list[Preference], list[Preference]]:
    """Récupère les préférences créées par l'utilisateur et celles partagées avec lui.

    Args:
        username: Nom d'utilisateur
        client_id: Client ID de l'application
        session: Session SQLAlchemy

    Returns:
        Tuple contenant :
        - Liste des préférences créées par l'utilisateur
        - Liste des préférences partagées avec l'utilisateur
    """
    # Préférences créées par l'utilisateur
    created_prefs = (
        session.query(Preference)
        .options(lazyload(Preference.shares))
        .filter_by(username=username, application_clientid=client_id)
        .order_by(Preference.id)
        .all()
    )

    # Préférences partagées avec l'utilisateur
    shared_prefs = (
        session.query(Preference)
        .join(Share)
        .filter(Share.shared_username_email == username, Preference.application_clientid == client_id)
        .distinct(Preference.id)
        .all()
    )

    return created_prefs, shared_prefs


async def get_preference_by_uuid(uuid: str, client_id: str, session: Session) -> Preference | None:
    """Récupère une préférence par son UUID.

    Args:
        uuid: UUID de la préférence
        client_id: Client ID de l'application
        session: Session SQLAlchemy

    Returns:
        La préférence si trouvée, None sinon
    """
    try:
        preference = (
            session.query(Preference)
            .filter(
                cast(Preference.uuid, sqlalchemy.String) == uuid,
                Preference.application_clientid == client_id,
            )
            .one()
        )
        return preference
    except sqlalchemy.exc.NoResultFound:
        return None


async def create_preference(
    username: str,
    client_id: str,
    name: str,
    filters: dict[str, Any],
    options: dict[str, Any] | None,
    shares_data: list[dict[str, str]],
    session: Session,
) -> Preference:
    """Crée une nouvelle préférence.

    Args:
        username: Nom d'utilisateur du créateur
        client_id: Client ID de l'application
        name: Nom de la préférence
        filters: Critères de filtrage
        options: Options supplémentaires (optionnel)
        shares_data: Liste des partages (dicts avec clé 'shared_username_email')
        session: Session SQLAlchemy

    Returns:
        La préférence créée
    """
    # Filtrer les shares pour exclure l'utilisateur lui-même
    filtered_shares = [share for share in shares_data if share.get("shared_username_email") != username]

    # Créer les objets Share
    share_objects = [Share(**share) for share in filtered_shares]

    # Créer la préférence
    preference = Preference(
        username=username,
        name=name,
        options=options,
        filters=filters,
        application_clientid=client_id,
    )
    preference.shares = share_objects

    session.add(preference)
    session.flush()

    logger.info(f"Préférence créée : {preference.uuid} par {username}")
    return preference


async def update_preference(
    uuid: str,
    username: str,
    client_id: str,
    name: str,
    filters: dict[str, Any],
    options: dict[str, Any] | None,
    shares_data: list[dict[str, str]],
    session: Session,
) -> Preference:
    """Met à jour une préférence existante.

    Args:
        uuid: UUID de la préférence à mettre à jour
        username: Nom d'utilisateur (pour vérifier la propriété)
        client_id: Client ID de l'application
        name: Nouveau nom
        filters: Nouveaux critères de filtrage
        options: Nouvelles options
        shares_data: Nouvelle liste des partages
        session: Session SQLAlchemy

    Returns:
        La préférence mise à jour

    Raises:
        ValueError: Si la préférence n'appartient pas à l'utilisateur
    """
    preference = await get_preference_by_uuid(uuid, client_id, session)

    if not preference:
        raise ValueError(f"Préférence {uuid} introuvable")

    if preference.username != username:
        raise ValueError("Vous n'avez pas les droits de modifier cette préférence")

    # Mise à jour des champs basiques
    preference.name = name
    preference.filters = filters
    preference.options = options

    # Gestion des partages
    # Filtrer pour exclure l'utilisateur lui-même
    filtered_shares = [share for share in shares_data if share.get("shared_username_email") != username]

    # Créer les nouveaux objets Share
    new_share_objects = [Share(**share) for share in filtered_shares]

    # Trouver les différences
    existing_emails = {s.shared_username_email for s in preference.shares}
    new_emails = {s.shared_username_email for s in new_share_objects}

    to_delete = existing_emails - new_emails
    to_add = new_emails - existing_emails

    # Supprimer les anciens partages
    for current_share in list(preference.shares):
        if current_share.shared_username_email in to_delete:
            session.delete(current_share)

    # Ajouter les nouveaux partages
    for new_share in new_share_objects:
        if new_share.shared_username_email in to_add:
            preference.shares.append(new_share)

    session.flush()

    logger.info(f"Préférence mise à jour : {preference.uuid}")
    return preference


async def delete_preference(uuid: str, username: str, client_id: str, session: Session) -> bool:
    """Supprime une préférence.

    Args:
        uuid: UUID de la préférence à supprimer
        username: Nom d'utilisateur (pour vérifier la propriété)
        client_id: Client ID de l'application
        session: Session SQLAlchemy

    Returns:
        True si la suppression a réussi

    Raises:
        ValueError: Si la préférence n'appartient pas à l'utilisateur
    """
    preference = await get_preference_by_uuid(uuid, client_id, session)

    if not preference:
        raise ValueError(f"Préférence {uuid} introuvable")

    if preference.username != username:
        raise ValueError("Vous n'avez pas les droits de supprimer cette préférence")

    session.delete(preference)
    session.commit()

    logger.info(f"Préférence supprimée : {uuid}")
    return True


async def increment_usage(preference: Preference, session: Session) -> None:
    """Incrémente le compteur d'utilisation et met à jour la date de dernier accès.

    Args:
        preference: La préférence à mettre à jour
        session: Session SQLAlchemy
    """
    try:
        preference.nombre_utilisation = (preference.nombre_utilisation or 0) + 1
        preference.dernier_acces = datetime.datetime.utcnow()
        session.commit()
    except Exception as e:
        logger.warning(f"Erreur lors de la mise à jour du compteur d'usage : {e}")
        session.rollback()
