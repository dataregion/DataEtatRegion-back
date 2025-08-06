from pydantic import BaseModel


class KeycloakOpenIdConfig(BaseModel):
    url: str
    realm: str
    client_id: str
    secret_key: str
    test_user: str
    test_password: str


class Config(BaseModel):
    sqlalchemy_database_uri: str
    """database url à la sqlalchemy: https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls"""
    print_sql: bool
    """Flag qui active le paramètre 'echo' de l'engine sqlalchemy"""

    keycloak_openid: KeycloakOpenIdConfig
