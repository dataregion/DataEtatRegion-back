import os
import pytest

from app import create_app_base, db

file_path = os.path.abspath(os.getcwd()) + "\database.db"
settings_path = os.path.abspath(os.getcwd()) + "\settings.db"
audit_path = os.path.abspath(os.getcwd()) + "\meta_audit.db"

extra_config = {
    "SQLALCHEMY_BINDS": {
        "settings": "sqlite:///" + settings_path,
        "audit": "sqlite:///" + audit_path,
    },
    "SQLALCHEMY_DATABASE_URI": "sqlite:///" + file_path,
    "SECRET_KEY": "secret",
    "OIDC_CLIENT_SECRETS": "ser",
    "TESTING": True,
    "SERVER_NAME": "localhost",
    "UPLOAD_FOLDER": "/tmp/",
}


test_app = create_app_base(extra_config_settings=extra_config)


@pytest.fixture(scope="session")
def app():
    return test_app


@pytest.fixture(scope="session")
def connections(app):
    with app.app_context():
        engine = db.engines[None]
        engine_settings = db.engines["settings"]
        engine_audit = db.engines["audit"]
        connections = {
            "database": engine.connect(),
            "settings": engine_settings.connect(),
            "audit": engine_audit.connect(),
        }

        yield connections

        connections["database"].close()
        connections["settings"].close()
        connections["audit"].close()
        # fermerture des connections et des bases
        db.session.close()
        engine.dispose()
        engine_settings.dispose()
        engine_audit.dispose()
        os.remove(file_path)
        os.remove(audit_path)
        os.remove(settings_path)


@pytest.fixture(scope="session")
def test_client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def database(app, connections, request):
    with app.app_context():
        db.create_all()
    return db


@pytest.fixture(autouse=True)
def session(connections, database, request):
    """retourne la session à la base de données principale"""

    session = db.session
    session.begin_nested()

    def teardown():
        session.expire_all()
        session.close_all()
        session.rollback()

    request.addfinalizer(teardown)
    return session
