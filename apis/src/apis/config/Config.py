from models.value_objects.redis_connection_info import RedisConnectionInfo
from models.value_objects.api_entreprise_info import ApiEntrepriseInfo
from models.value_objects.api_data_subvention_info import ApiDataSubventionInfo
from models.value_objects.ratelimiter_info import RateLimiterInfo
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

class Config(BaseModel):
    sqlalchemy_database_uri: str
    """database url à la sqlalchemy: https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls"""
    print_sql: bool
    """Flag qui active le paramètre 'echo' de l'engine sqlalchemy"""

    keycloak_openid: KeycloakOpenIdConfig
    
    cache_config: CacheConfig
    
    redis_applicatif: RedisConnectionInfo

    api_data_subventions: ApiDataSubventionInfo

    api_entreprise: ApiEntrepriseInfo
    api_entreprise_ratelimiter: RateLimiterInfo

    api_entreprise_batch: ApiEntrepriseInfo
    api_entreprise_batch_ratelimiter: RateLimiterInfo

    """Token d'authentification pour les plugins Grist"""
    token_for_grist_plugins: str

    to_superset_config: ToSupersetConfig
