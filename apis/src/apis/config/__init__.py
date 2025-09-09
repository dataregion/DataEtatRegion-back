from functools import cached_property
import os

import yaml

from .Config import Config


class _ConfigFile:
    """Représente le fichier de configuration apis actuel"""

    def __init__(self, path: str | None = None) -> None:

        if path is None:
            self.path = os.path.join(os.path.dirname(__file__), "config.yml")
        else:
            self.path = path

    @cached_property
    def config(self):
        with open(self.path) as yamlfile:
            config_data = yaml.load(yamlfile, Loader=yaml.FullLoader)
        config = Config(**config_data)
        return config
