from pathlib import Path
from batches.config.current import get_config


def get_dossier_exports_path() -> Path:
    return get_config().dossier_des_exports
