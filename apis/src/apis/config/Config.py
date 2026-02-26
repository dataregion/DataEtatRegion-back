from pathlib import Path
from models.value_objects.redis_connection_info import RedisConnectionInfo
from models.value_objects.api_entreprise_info import ApiEntrepriseInfo
from models.value_objects.api_data_subvention_info import ApiDataSubventionInfo
from pydantic import BaseModel, Field


class KeycloakOpenIdConfig(BaseModel):
    url: str
    realm: str
    client_id: str
    secret_key: str
    test_user: str | None = Field(
        default=None,
        description="For tests only - give a test user to authenticate with",
    )
    test_password: str | None = Field(
        default=None,
        description="For tests only - give a test user to authenticate with",
    )

class ToSupersetConfig(BaseModel):
    url_superset: str # l'url public du superset
    user_superset_tech_login: str # l'utilisateur technique Superset (qui a les droits admin)
    user_superset_tech_password: str
    superset_database_id: int #L'Id de la datasource où les datasets seront créé (d)
    db_schema_export : str = Field(default='grist_data') # le nom du schema où seront créer les tables en base de données
    superset_catalog: str = Field(default='CHORUS')  # le nom du catalog dans superset où seront identifiable les données


class CacheConfig(BaseModel):
    budget_totaux_enabled: bool = Field(
        default = True,
        description="Le caching pour le calcul des totaux de l'api de consultation budget"
    )
    budget_totaux_size: int = Field(
        default=10_000,
        description="Taille du cache pour les totaux des lignes budgetaires"
    )

class UploadConfig(BaseModel):
    tus_folder: str = Field(required=True, description="Chemin du dossier de sauvegarde des fichiers uploadés")
    final_folder: str = Field(required=True, description="Dossier où seront mis les fichiers budgets chorus à traiter")
    max_size: int = Field(default=1_000_000_000, description="Taille maximale des fichiers uploadés (ex: 1G)")
    

class Config(BaseModel):
    print_sql: bool
    """Flag qui active le paramètre 'echo' de l'engine sqlalchemy"""

    sqlalchemy_database_uri: str
    """Base de données principale"""

    sqlalchemy_database_uri_audit: str
    """Base de données d'audit (utilisée avec le bind)"""

    sqlalchemy_database_uri_settings: str
    """Base de données settings (schéma pour préférences utilisateurs, etc.)"""

    dossier_des_exports: Path
    """Chemin vers le répertoire qui contient les exports utilisateurs."""

    keycloak_openid: KeycloakOpenIdConfig

    keycloak_administrator: KeycloakOpenIdConfig
    """Utilisateur administrateur de keycloak pour la gestion des utilisateurs et des groupes (création, suppression, etc.)"""
    
    cache_config: CacheConfig
    
    redis_applicatif: RedisConnectionInfo

    api_data_subventions: ApiDataSubventionInfo

    api_entreprise: ApiEntrepriseInfo

    api_entreprise_batch: ApiEntrepriseInfo

    token_for_grist_plugins: str
    """Token d'authentification pour les plugins Grist"""

    to_superset_config: ToSupersetConfig

    upload: UploadConfig
