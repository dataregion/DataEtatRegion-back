import logging

_format = "%(asctime)s.%(msecs)03d : %(levelname)s : %(message)s"
logging.basicConfig(format=_format, datefmt="%Y-%m-%d %H:%M:%S", level=logging.INFO, force=True)


def setLogLevel(level: int | str) -> None:
    """
    Configure le niveau de log pour l'application.

    Args:
        level: Niveau de log (int ou str). Peut être:
               - Un entier (ex: 10, 20, 30, 40, 50)
               - Un nom de niveau (ex: "DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")

    Examples:
        >>> from apis import setLogLevel
        >>> setLogLevel("DEBUG")
        >>> setLogLevel(logging.INFO)
    """
    if isinstance(level, str):
        level = level.upper()

    logging.getLogger().setLevel(level)
    logging.info(f"Niveau de log configuré à: {logging.getLevelName(logging.getLogger().level)}")


# Appliquer le niveau de log depuis la configuration au démarrage
def _apply_config_log_level():
    """Charge la configuration et applique le niveau de log défini dans config.yml"""
    try:
        # Import différé pour éviter les imports circulaires
        from apis.config.current import get_config

        config = get_config()
        if hasattr(config, "log_level") and config.log_level:
            setLogLevel(config.log_level)
    except Exception as e:
        logging.warning(f"Impossible d'appliquer le niveau de log depuis la configuration: {e}")


# Appliquer automatiquement le niveau de log au démarrage
_apply_config_log_level()
