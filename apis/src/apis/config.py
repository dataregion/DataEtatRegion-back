import os
import yaml


def read_config():
    try:
        config_path = os.path.join(os.path.dirname(__file__), "config", "config.yml")
        with open(config_path) as yamlfile:
            config_data = yaml.load(yamlfile, Loader=yaml.FullLoader)
    except Exception:
        config_data = {}
    return config_data


config = read_config()
