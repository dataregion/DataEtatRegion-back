"""Helper pour l'initialisation du service d'envoi d'emails dans les flows Prefect."""

from functools import lru_cache

from services.mail.mail import Mail

from batches.config.current import get_config


@lru_cache
def get_mail_service() -> Mail:
    """Initialise et retourne le service Mail configuré pour l'envoi d'emails.

    Returns:
        Mail: Instance du service Mail configuré avec les paramètres SMTP.
    """
    smtp_config = get_config().smtp

    return Mail(
        server=smtp_config.server,
        port=smtp_config.port,
        from_email=smtp_config.from_email,
        use_ssl=smtp_config.use_ssl,
        pwd=smtp_config.pwd,
        login=smtp_config.login,
    )
