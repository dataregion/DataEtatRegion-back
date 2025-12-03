import os
from fastapi.params import Depends
from pydantic import BaseModel
from typing_extensions import Annotated
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
import yaml
from typing import Optional


class KeycloakOpenIdConfig(BaseModel):
    url: str
    realm: str
    client_id: str


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # URLs de synchronisation
    url_init_sync_db: str = "http://localhost:5000/budget/api/v1/sync-referentiels"
    url_sync_db: str = "http://localhost:5000/budget/api/v1/sync-referentiels"
    token_sync_db: str = "GgqZ7LhmBOPsfJo9zH2aRTtJlzy9PV5G"

    url_superset: str = "http://superset"

    url_to_superset_api: str = "http://localhost:8050/grist-to-superset/api/v3/import/table"
    url_token_to_superset: str = "X-TOKEN-TO-SUPERSET"
    timeout_api_calls: int | None = 30  # secondes

    keycloak: KeycloakOpenIdConfig
    # Mode développement
    dev_mode: bool = True

    @classmethod
    def load_from_yaml(cls, config_path: Optional[Path] = None) -> "Settings":
        """
        Charge les settings depuis un fichier YAML s'il existe,
        sinon utilise les valeurs par défaut et les variables d'environnement.

        Priorité :
        1. Paramètre config_path explicite
        2. Variable d'environnement CONFIG_PATH
        3. Chemins par défaut (config.yml, etc.)
        """
        # 1. Si config_path est fourni explicitement
        if config_path is not None:
            if config_path.exists():
                return cls._load_yaml_file(config_path)
            else:
                print(f"⚠️  Fichier de config spécifié introuvable: {config_path}")
                return cls()

        # 2. Vérifier la variable d'environnement CONFIG_PATH
        env_config_path = os.getenv("CONFIG_PATH", "config.yml")
        if env_config_path:
            config_path = Path(env_config_path)
            if config_path.exists():
                return cls._load_yaml_file(config_path)
            else:
                print(f"⚠️  CONFIG_PATH défini mais fichier introuvable: {config_path}")
                return cls()

        # 3. Essayer les chemins par défaut
        possible_paths = [
            Path("config.yml"),
            Path("config.yaml"),
            Path("settings.yml"),
            Path("settings.yaml"),
        ]
        config_path = next((p for p in possible_paths if p.exists()), None)

        if config_path is None:
            print("ℹ️  Aucun fichier de config trouvé, utilisation des valeurs par défaut")
            return cls()

        return cls._load_yaml_file(config_path)

    @classmethod
    def _load_yaml_file(cls, config_path: Path) -> "Settings":
        """Charge et parse un fichier YAML."""
        print(f"✓ Configuration chargée depuis: {config_path}")

        with open(config_path, "r", encoding="utf-8") as f:
            yaml_data = yaml.safe_load(f) or {}

        return cls(**yaml_data)


# Instance globale des settings
settings = Settings.load_from_yaml()


# Fonction de dépendance
def get_settings() -> Settings:
    """Dépendance FastAPI pour injecter les settings."""
    return settings


SettingsDep = Annotated[Settings, Depends(get_settings)]
