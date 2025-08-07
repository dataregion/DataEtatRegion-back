import os
from functools import lru_cache
from . import _ConfigFile

OVERRIDES = { }

@lru_cache
def get_config():
    """Current configuration of the application"""
    config_filep = os.environ.get("APIS_CONFIG_PATH", "./config/config.yml")
    config = _ConfigFile(config_filep).config
    for key, val in OVERRIDES.items():
        setattr(config, key, val)
    return config

def override_config(key: str, value):
    """Override a configuration on runtime"""
    OVERRIDES[key] = value
    get_config.cache_clear()