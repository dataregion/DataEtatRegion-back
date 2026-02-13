"""Flow Prefect pour l'envoi d'emails de partage de préférences utilisateurs.

Ce flow remplace la tâche Celery `share_filter_user` et permet d'envoyer
des emails de notification lorsqu'un utilisateur partage ses préférences
avec d'autres utilisateurs.
"""

from datetime import datetime
from datetime import timezone

import sqlalchemy
from prefect import flow, task, get_run_logger
from prefect.cache_policies import NO_CACHE
from sqlalchemy import cast
from sqlalchemy.orm import lazyload

from batches.database import session_settings_scope
from batches.mail import get_mail_service
from models.entities.preferences.Preference import Preference


TEXT_TEMPLATE = (
    "Bonjour,"
    "{0} souhaite vous partager un tableau de bord via le service {1} de votre région."
    "{1} est une solution interministérielle pilotée par les préfectures de région. "
    "Elle vise au partage et à la réutilisation de données financières de l'État."
    "Pour y accéder, veuillez cliquer sur le lien {2} et vous connecter."
    "Si vous n'avez pas de compte, vous pouvez faire une demande en suivant le lien {3}."
    ""
)

HTML_TEMPLATE = """
<h3>Bonjour,</h3>

<p>{0} souhaite vous partager un tableau de bord via le service {1} de votre région.</p>
<p>{1} est une solution interministérielle pilotée par les préfectures de région. 
Elle vise au partage et à la réutilisation de données financières de l'État.</p>
<p>Pour y accéder, veuillez cliquer sur ce <a href="{2}">lien</a> et vous connecter.</p>
<p>Si vous n'avez pas de compte, vous pouvez faire une demande en suivant ce <a href="{3}">lien</a></p>
"""

SUBJECT_BUDGET = "Budget Data État"
SUBJECT_FRANCE_RELANCE = "France Relance"


def _get_subject(link: str) -> str:
    """Détermine le sujet de l'email en fonction de l'URL.

    Args:
        link: URL de l'application (host_link)

    Returns:
        Le sujet approprié pour l'email
    """
    if "relance" in link:
        return SUBJECT_FRANCE_RELANCE
    return SUBJECT_BUDGET


@task(
    timeout_seconds=120,
    log_prints=True,
    cache_policy=NO_CACHE,
    retries=0,  # Pas de retry car c'est une tâche non idempotente
)
def send_share_emails(preference_uuid: str, host_link: str):
    """Tâche Prefect pour envoyer les emails de partage de préférence.

    Récupère une préférence par son UUID, puis envoie un email à chaque
    destinataire qui n'a pas encore reçu de notification.

    Args:
        preference_uuid: UUID de la préférence à partager
        host_link: URL de l'application pour construire les liens de partage
    """
    logger = get_run_logger()
    logger.info(f"[SHARE][FILTER] Start preference {preference_uuid}")

    # Récupérer le service mail
    mail_service = get_mail_service()

    # Ouvrir une session sur la base settings
    with session_settings_scope() as session:
        with session.begin():
            # Requêter la préférence avec ses partages
            preference = (
                session.query(Preference)
                .options(lazyload(Preference.shares))
                .filter(cast(Preference.uuid, sqlalchemy.String) == preference_uuid)
                .one_or_none()
            )

            if preference is None:
                logger.warning(f"[SHARE][FILTER] Preference {preference_uuid} not found")
                return

            if len(preference.shares) == 0:
                logger.info(f"[SHARE][FILTER] No shares for preference {preference_uuid}")
                return

            # Construire les liens
            link_preference = f"{host_link}/?uuid={preference_uuid}"
            link_register = f"{host_link}/register"
            subject = _get_subject(host_link)

            # Envoyer un email pour chaque partage non encore envoyé
            emails_sent = 0
            for share in preference.shares:
                if not share.email_send:
                    # Formater les templates
                    txt = TEXT_TEMPLATE.format(
                        preference.username,
                        subject,
                        link_preference,
                        link_register,
                    )
                    htm = HTML_TEMPLATE.format(
                        preference.username,
                        subject,
                        link_preference,
                        link_register,
                    )

                    # Marquer comme envoyé
                    share.email_send = True
                    share.date_email_send = datetime.now(timezone.utc)

                    emails_sent += 1

                    # Envoyer l'email
                    mail_service.send_email(subject, share.shared_username_email, txt, htm)

                    logger.debug(f"[SHARE][FILTER] Sent email to {share.shared_username_email}")

            # Commit des changements
            logger.info(f"[SHARE][FILTER] Completed: {emails_sent} email(s) sent for preference {preference_uuid}")


@flow(log_prints=True)
def share_filter_user(preference_uuid: str, host_link: str):
    """Flow Prefect pour partager une préférence utilisateur par email.

    Ce flow remplace la tâche Celery `share_filter_user`. Il envoie des emails
    de notification aux utilisateurs avec lesquels une préférence a été partagée.

    Args:
        preference_uuid: UUID de la préférence à partager
        host_link: URL de base de l'application pour construire les liens
    """
    send_share_emails(preference_uuid, host_link)
