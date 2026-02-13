from fastapi.security import OAuth2PasswordBearer
import pytest

from apis.app import create_app
from apis.config.current import get_config, override_config
from services.tests.DataEtatPostgresContainer import DataEtatPostgresContainer
from models.connected_user import ConnectedUser
from models import Base

from sqlalchemy import create_engine, text


def init_db_schemas(test_db, config):
    """Initialise le schéma de base de données selon SQLAlchemy."""
    # Créer les engines pour chaque base de données
    main_engine = create_engine(config.sqlalchemy_database_uri)
    audit_engine = create_engine(config.sqlalchemy_database_uri_audit, connect_args={"options": "-c search_path=audit"})
    settings_engine = create_engine(
        config.sqlalchemy_database_uri_settings, connect_args={"options": "-c search_path=settings"}
    )

    with main_engine.connect() as conn:
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS audit;"))
        conn.execute(text("CREATE SCHEMA IF NOT EXISTS settings;"))
        conn.commit()

    main_tables = [table for table in Base.metadata.tables.values() if table.schema is None]
    Base.metadata.create_all(main_engine, tables=main_tables)

    audit_tables = [table for table in Base.metadata.tables.values() if table.schema == "audit"]
    Base.metadata.create_all(audit_engine, tables=audit_tables)

    settings_table = [table for table in Base.metadata.tables.values() if table.schema == "settings"]
    Base.metadata.create_all(settings_engine, tables=settings_table)


@pytest.fixture(scope="session")
def test_db():
    postgres_container = DataEtatPostgresContainer()
    postgres_container.start()
    override_config("sqlalchemy_database_uri", postgres_container.get_connection_url())
    override_config(
        "sqlalchemy_database_uri_audit", f"{postgres_container.get_connection_url()}?options=-c%20search_path=audit"
    )
    override_config(
        "sqlalchemy_database_uri_settings",
        f"{postgres_container.get_connection_url()}?options=-c%20search_path=settings",
    )

    init_db_schemas(postgres_container, get_config())

    yield postgres_container
    postgres_container.stop(force=True, delete_volume=True)


@pytest.fixture(scope="session")
def config(test_db):
    return get_config()


@pytest.fixture(scope="session")
def mock_connected_user():
    """Crée un ConnectedUser pour les tests."""
    return ConnectedUser(
        {
            "azp": "test-client-id",
            "sub": "test-user-123",
            "email": "test@example.com",
            "preferred_username": "testuser",
            "realm_access": {"roles": ["user", "admin"]},
            "resource_access": {
                "test-client-id": {"roles": ["users"]},
            },
        }
    )


@pytest.fixture(scope="session")
def patch_keycloak_validator(mock_connected_user):
    """Patch KeycloakTokenValidator pour les tests."""
    from apis.security.keycloak_token_validator import KeycloakTokenValidator

    #
    # On stub le traitement du flow oauth2password bearer pour les tests
    #
    original_validate_token = KeycloakTokenValidator.validate_token
    original_oauth2passwordbearer = OAuth2PasswordBearer.__call__

    async def stub_call(self, request):
        return None

    async def mocked_validate_token(self, token):
        return mock_connected_user

    OAuth2PasswordBearer.__call__ = stub_call
    KeycloakTokenValidator.validate_token = mocked_validate_token

    yield

    OAuth2PasswordBearer.__call__ = original_oauth2passwordbearer
    KeycloakTokenValidator.validate_token = original_validate_token


@pytest.fixture(scope="session")
def app(test_db, config):
    app = create_app()
    return app
