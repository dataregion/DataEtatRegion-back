import yaml


def read_config():
    try:
        with open("config/config.yml") as yamlfile:
            config_data = yaml.load(yamlfile, Loader=yaml.FullLoader)
    except Exception:
        config_data = {}
    return config_data

def read_config_oidc():
    try:
        with open("config/oidc.yml") as yamlfile:
            config_data = yaml.load(yamlfile, Loader=yaml.FullLoader)
    except Exception:
        config_data = {}
    return config_data


config = read_config()
config_oidc = read_config_oidc()
