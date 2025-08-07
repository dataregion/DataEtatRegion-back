import os
from functools import lru_cache
from . import _ConfigFile


@lru_cache
def get_config():
    """Current configuration of the application"""
    config_filep = os.environ.get("APIS_CONFIG_PATH", "./config/config.yml")
    config = _ConfigFile(config_filep).config
    return config