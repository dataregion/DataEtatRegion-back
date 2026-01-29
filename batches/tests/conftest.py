import contextlib
from services.tests.DataEtatPostgresContainer import DataEtatPostgresContainer
from sqlalchemy import delete
from batches import database
from batches.config.current import get_config

postgres = DataEtatPostgresContainer()
postgres.start()
TEST_DB_URL = postgres.get_connection_url()

get_config().sqlalchemy_database_uri = TEST_DB_URL
get_config().sqlalchemy_database_uri_audit = TEST_DB_URL


from sqlalchemy.orm import declarative_base
from models import init as init_persistence_module

Base = declarative_base()
init_persistence_module(base=Base)


from models.entities.common.Tags import TagAssociation, Tags
from models.entities.financial import Ademe, FinancialAe, FinancialCp, France2030
from models.entities.refs import (
    CentreCouts,
    DomaineFonctionnel,
    FournisseurTitulaire,
    GroupeMarchandise,
    LocalisationInterministerielle,
    Qpv,
    ReferentielProgrammation,
)
from models.entities.refs.CodeProgramme import CodeProgramme
from models.entities.refs.Region import Region
from models.entities.refs.Siret import Siret

from batches.database import get_session_maker
import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    SessionMaker = get_session_maker("main")
    engine = SessionMaker.kw["bind"]

    Base.metadata.create_all(engine)

    yield

    postgres.stop()


@pytest.fixture(scope="function")
def session():
    SessionMaker = get_session_maker("main")
    engine = SessionMaker.kw["bind"]

    connection = engine.connect()
    transaction = connection.begin()

    session = SessionMaker(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture
def patch_session_scope(session, monkeypatch):
    @contextlib.contextmanager
    def _session_scope_override():
        yield session

    monkeypatch.setattr(
        database,
        "session_scope",
        _session_scope_override,
    )
    

def get_or_create(session, model, **kwargs):
    """
    Helper function to get an existing object or create a new one.
    """
    instance = session.query(model).filter_by(**kwargs).one_or_none()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        return instance


def add_references(entity, session, region=None):
    # Using the helper function to get or create related objects
    # Dans le cas ou l'entité est une AE
    if hasattr(entity, "programme") and entity.programme:
        get_or_create(session, CodeProgramme, code=entity.programme)
    if hasattr(entity, "centre_couts") and entity.centre_couts:
        get_or_create(session, CentreCouts, code=entity.centre_couts)
    if hasattr(entity, "domaine_fonctionnel") and entity.domaine_fonctionnel:
        get_or_create(session, DomaineFonctionnel, code=entity.domaine_fonctionnel)
    if hasattr(entity, "fournisseur_titulaire") and entity.fournisseur_titulaire:
        get_or_create(session, FournisseurTitulaire, code=entity.fournisseur_titulaire)
    if hasattr(entity, "fournisseur_paye") and entity.fournisseur_paye:
        get_or_create(session, FournisseurTitulaire, code=entity.fournisseur_paye)
    if hasattr(entity, "groupe_marchandise") and entity.groupe_marchandise:
        get_or_create(session, GroupeMarchandise, code=entity.groupe_marchandise)
    if hasattr(entity, "localisation_interministerielle") and entity.localisation_interministerielle:
        get_or_create(session, LocalisationInterministerielle, code=entity.localisation_interministerielle)
    if hasattr(entity, "referentiel_programmation") and entity.referentiel_programmation:
        get_or_create(session, ReferentielProgrammation, code=entity.referentiel_programmation)
    if hasattr(entity, "siret") and entity.siret and entity.siret != "#":
        get_or_create(session, Siret, code=entity.siret)
    if region:
        get_or_create(session, Region, code=region)

    # Dans le cas ou l'entitié est une ligne ADEME
    ademe: Ademe = entity
    if hasattr(entity, "siret_attribuant"):
        get_or_create(session, Siret, code=ademe.siret_attribuant)
    if hasattr(entity, "siret_beneficiaire"):
        get_or_create(session, Siret, code=ademe.siret_beneficiaire)

    session.commit()


def delete_references(session):
    # Suppression des objets après le test
    session.execute(delete(TagAssociation))
    session.execute(delete(Tags))
    session.execute(delete(FinancialCp))
    session.execute(delete(FinancialAe))
    session.execute(delete(CodeProgramme))
    session.execute(delete(CentreCouts))
    session.execute(delete(DomaineFonctionnel))
    session.execute(delete(FournisseurTitulaire))
    session.execute(delete(GroupeMarchandise))
    session.execute(delete(LocalisationInterministerielle))
    session.execute(delete(ReferentielProgrammation))
    session.execute(delete(Region))
    session.execute(delete(Ademe))
    session.execute(delete(France2030))
    session.execute(delete(Siret))
    session.execute(delete(Qpv))

    session.commit()
