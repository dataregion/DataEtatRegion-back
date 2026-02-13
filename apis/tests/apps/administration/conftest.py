"""Fixtures pour les tests du module administration."""

from ...fixtures.app import (
    app as _test_app,  # noqa: F401
    patch_keycloak_validator,  # noqa: F401
)

import uuid
from datetime import datetime, timezone

import pytest
from sqlalchemy.orm import Session

from apis.database import get_session_settings
from models.entities.preferences.Preference import Preference, Share

########################################################
#


@pytest.fixture(scope="session")
def app(_test_app, patch_keycloak_validator):  # noqa: F811
    return _test_app


########################################################


@pytest.fixture
def session_settings():
    """Session pour la base de données settings.

    Cette fixture crée une session vers la base settings où sont stockées
    les préférences utilisateur et leurs partages.
    """
    gen = get_session_settings()
    session = next(gen)
    try:
        yield session
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


@pytest.fixture
def shared_preference(session_settings: Session, mock_connected_user):
    """Crée une préférence de test avec un partage en base de données.

    Cette préférence appartient à l'utilisateur mocké et est partagée avec
    un autre utilisateur (autre@example.com).
    """
    # Créer la préférence
    pref = Preference(
        uuid=str(uuid.uuid4()),
        username=mock_connected_user.email,
        name="Préférence Partagée",
        application_clientid=mock_connected_user.azp,
        filters={"annee": 2024, "region": "Bretagne"},
        options={"columns": ["nom", "montant"], "sort": "asc"},
        date_creation=datetime.now(timezone.utc),
        nombre_utilisation=0,
    )
    session_settings.add(pref)
    session_settings.flush()  # Pour obtenir l'id

    # Créer le partage
    share = Share(
        preference_id=pref.id,
        shared_username_email="autre@example.com",
        email_send=False,
    )
    session_settings.add(share)
    session_settings.commit()
    session_settings.refresh(pref)

    yield pref

    # Cleanup
    session_settings.delete(pref)
    session_settings.commit()


@pytest.fixture
def unshared_preference(session_settings: Session, mock_connected_user):
    """Crée une préférence de test sans partage en base de données.

    Cette préférence appartient à l'utilisateur mocké et n'est pas partagée.
    """
    pref = Preference(
        uuid=str(uuid.uuid4()),
        username=mock_connected_user.email,
        name="Préférence Non Partagée",
        application_clientid=mock_connected_user.azp,
        filters={"annee": 2025, "departement": "35"},
        options={"view": "table"},
        date_creation=datetime.now(timezone.utc),
        nombre_utilisation=5,
    )
    session_settings.add(pref)
    session_settings.commit()
    session_settings.refresh(pref)

    yield pref

    # Cleanup
    session_settings.delete(pref)
    session_settings.commit()


@pytest.fixture
def other_user_preference(session_settings: Session, mock_connected_user):
    """Crée une préférence appartenant à un autre utilisateur.

    Utile pour tester les contrôles d'autorisation (ne pas pouvoir modifier/supprimer
    les préférences des autres).
    """
    pref = Preference(
        uuid=str(uuid.uuid4()),
        username="otheruser",
        name="Préférence d'un autre",
        application_clientid=mock_connected_user.azp,
        filters={"test": "value"},
        options={},
        date_creation=datetime.now(timezone.utc),
        nombre_utilisation=0,
    )
    session_settings.add(pref)
    session_settings.commit()
    session_settings.refresh(pref)

    yield pref

    # Cleanup
    session_settings.delete(pref)
    session_settings.commit()


@pytest.fixture
def preference_shared_with_user(session_settings: Session, mock_connected_user):
    """Crée une préférence partagée AVEC l'utilisateur de test.

    Cette préférence appartient à un autre utilisateur mais est partagée
    avec l'utilisateur mocké.
    """
    # Créer la préférence (appartient à quelqu'un d'autre)
    pref = Preference(
        uuid=str(uuid.uuid4()),
        username="shareowner",
        name="Préférence Partagée Avec Moi",
        application_clientid=mock_connected_user.azp,
        filters={"shared": True},
        options={},
        date_creation=datetime.now(timezone.utc),
        nombre_utilisation=0,
    )
    session_settings.add(pref)
    session_settings.flush()

    # Partager avec l'utilisateur de test
    share = Share(
        preference_id=pref.id,
        shared_username_email=mock_connected_user.email,
        email_send=True,
        date_email_send=datetime.now(timezone.utc),
    )
    session_settings.add(share)
    session_settings.commit()
    session_settings.refresh(pref)

    yield pref

    # Cleanup
    session_settings.delete(pref)
    session_settings.commit()
