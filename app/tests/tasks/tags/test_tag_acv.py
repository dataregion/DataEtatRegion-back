import json
import datetime
from models.entities.common.Tags import Tags
from models.entities.financial.Ademe import Ademe
import pytest
from sqlalchemy import delete

from models.entities.refs.CentreCouts import CentreCouts
from models.entities.refs.CodeProgramme import CodeProgramme
from models.entities.refs.Commune import Commune
from models.entities.refs.DomaineFonctionnel import DomaineFonctionnel
from models.entities.refs.FournisseurTitulaire import FournisseurTitulaire
from models.entities.refs.GroupeMarchandise import GroupeMarchandise
from models.entities.refs.LocalisationInterministerielle import LocalisationInterministerielle
from models.entities.refs.ReferentielProgrammation import ReferentielProgrammation
from models.entities.refs.Region import Region
from models.entities.refs.Siret import Siret
from models.entities.financial.FinancialAe import FinancialAe
from models.entities.common.Tags import TagAssociation
from app.tasks.tags.apply_tags import apply_tags_acv
from tests import delete_references
from tests.tasks.tags import TAG_ACV, TAG_DUMMY


@pytest.fixture(scope="function")
def tag_acv(database):
    tags = Tags(**TAG_ACV)  # noqa: F405
    database.session.add(tags)
    database.session.commit()
    yield tags
    database.session.execute(database.delete(TagAssociation))
    database.session.execute(database.delete(Tags))
    database.session.commit()


@pytest.fixture(scope="function")
def add_commune_and_siret_pontivy(database):
    # Commune pontivy
    commune = Commune(
        **{
            "id": "111",
            "code": "56178",
            "label_commune": "Pontivy",
            "code_departement": "56",
            "is_acv": True,
            "date_acv": None,
        }
    )

    siret = Siret(**{"code": "90933627300000", "code_commune": "56178", "denomination": "TEST"})

    database.session.add(commune)
    database.session.add(siret)

    database.session.commit()

    yield (
        commune,
        siret,
    )

    database.session.execute(database.delete(Siret))
    database.session.execute(database.delete(Commune))
    database.session.commit()


@pytest.fixture(scope="function")
def add_commune_pontivy(database):
    commune = database.session.query(Commune).filter_by(code="56178").one_or_none()

    if not commune:
        commune = Commune(
            **{
                "id": "111",
                "code": "56178",
                "label_commune": "Pontivy",
                "code_departement": "56",
                "is_acv": True,
                "date_acv": None,
            }
        )
        database.session.add(commune)
        database.session.commit()

    yield commune
    database.session.execute(database.delete(Commune))
    database.session.commit()


@pytest.fixture(scope="function")
def add_siret_pontivy(database):
    siret = database.session.query(Siret).filter_by(code="90933627300000").one_or_none()

    if not siret:
        siret = Siret(**{"code": "90933627300000", "code_commune": "56178", "denomination": "TEST"})
        database.session.add(siret)
        database.session.commit()

    yield siret

    # Suppression de l'objet après le test, uniquement si l'objet a été créé par cette fixture
    if siret and siret.code == "90933627300000":
        database.session.execute(database.delete(siret))
        database.session.commit()


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


@pytest.fixture(scope="function")
def insert_financial_ae_for_tag_acv(database, session):
    with session.no_autoflush:
        ae = session.query(FinancialAe).filter_by(n_ej="1", n_poste_ej=1).one_or_none()
        if not ae:
            ae = FinancialAe(
                annee=2020,
                n_ej="1",
                n_poste_ej=1,
                programme="380",
                domaine_fonctionnel="0380-01-01",
                centre_couts="BG00\\/DREETS0035",
                referentiel_programmation="BG00\\/010300000108",
                fournisseur_titulaire="1001465507",
                siret="90933627300000",
                localisation_interministerielle="N35",
                groupe_marchandise="groupe",
                date_modification_ej=datetime.datetime.now(),
                compte_budgetaire="co",
                data_source="REGION",
            )
            session.add(ae)

        add_references(ae, session)

        yield ae
        delete_references(session)


@pytest.fixture(scope="function")
def insert_financial_ae_for_other_tag(database, session):
    with session.no_autoflush:
        ae = session.query(FinancialAe).filter_by(n_ej="2", n_poste_ej=1).one_or_none()
        if not ae:
            ae = FinancialAe(
                annee=2020,
                n_ej="2",
                n_poste_ej=1,
                programme="200",
                domaine_fonctionnel="0380-01-02",
                centre_couts="BG00\\/DREETS0036",
                referentiel_programmation="BG00\\/010300000200",
                fournisseur_titulaire="1001465508",
                localisation_interministerielle="N36",
                siret="90933627300000",
                groupe_marchandise="groupe1",
                date_modification_ej=datetime.datetime.now(),
                compte_budgetaire="co",
                data_source="REGION",
            )
            session.add(ae)

        add_references(ae, session)

        yield ae
        delete_references(session)


def test_apply_acv_when_no_tag(
    database,
    session,
    add_commune_and_siret_pontivy,
    insert_financial_ae_for_tag_acv,
    insert_financial_ae_for_other_tag,
    tag_acv,
):
    # DO
    apply_tags_acv(tag_acv.type, None, None)  # type: ignore

    # assert
    tag_assocation: TagAssociation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_acv.id, TagAssociation.financial_ae == insert_financial_ae_for_tag_acv.id
        )
    ).scalar_one_or_none()
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_ae == insert_financial_ae_for_tag_acv.id
    assert tag_assocation.auto_applied is True

    session.execute(delete(TagAssociation))
    session.commit()

    delete_references(session)


def test_should_apply_tag_if_other_tag_associated(
    database, session, tag_acv, add_commune_and_siret_pontivy, insert_financial_ae_for_tag_acv: FinancialAe
):
    # given
    tags_dummy = Tags(**TAG_DUMMY)  # noqa: F405
    tag_assoc = TagAssociation(**{"financial_ae": insert_financial_ae_for_tag_acv.id, "auto_applied": False})
    tag_assoc.tag = tags_dummy
    session.add(tag_assoc)
    session.commit()

    # DO
    apply_tags_acv(tag_acv.type, None, None)  # type: ignore

    # ASSERT
    # Rechercher les associations avec financial_ae et s'assurer qu'il n'y en a que deux
    tag_assocations = (
        database.session.execute(
            database.select(TagAssociation).where(TagAssociation.financial_ae == insert_financial_ae_for_tag_acv.id)
        )
        .scalars()
        .fetchall()
    )

    assert len(tag_assocations) == 2, f"Expected 2 TagAssociations, but found {len(tag_assocations)}"

    tag_ids = {tag_assocations[0].tag_id, tag_assocations[1].tag_id}
    expected_tag_ids = {tags_dummy.id, tag_acv.id}

    assert tag_ids == expected_tag_ids, f"Expected Tag IDs {expected_tag_ids}, but found {tag_ids}"

    for t in tag_assocations:
        assert t.financial_ae == insert_financial_ae_for_tag_acv.id


def test_should_not_apply_tag_if_already_present(
    database, session, tag_acv, add_commune_and_siret_pontivy, insert_financial_ae_for_tag_acv
):
    # given affection du tag acv à l'AE
    tag_assoc = TagAssociation(
        **{
            "tag_id": tag_acv.id,
            "financial_ae": insert_financial_ae_for_tag_acv.id,
            "auto_applied": False,
        }
    )
    session.add(tag_assoc)
    session.commit()

    # DO
    apply_tags_acv(tag_acv.type, None, None)  # type: ignore

    # ASSERT
    tag_assocation = database.session.execute(
        database.select(TagAssociation).where(TagAssociation.tag_id == tag_acv.id)
    ).scalar_one_or_none()
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_ae == insert_financial_ae_for_tag_acv.id
    assert not tag_assocation.auto_applied


def test_should_apply_tag_if_context_is_ok(
    database, tag_acv, add_commune_and_siret_pontivy, insert_financial_ae_for_tag_acv
):
    # DO
    context = {"only": "FINANCIAL_DATA_AE", "id": insert_financial_ae_for_tag_acv.id}
    apply_tags_acv(tag_acv.type, None, json.dumps(context))  # type: ignore

    # ASSERT
    tag_assocation: TagAssociation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_acv.id, TagAssociation.financial_ae == insert_financial_ae_for_tag_acv.id
        )
    ).scalar_one_or_none()
    assert tag_assocation is not None
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_cp is None
    assert tag_assocation.financial_ae == insert_financial_ae_for_tag_acv.id
    assert tag_assocation.auto_applied is True


def test_should_not_apply_tag_if_context_is_not_ok(
    database, session, tag_acv, add_commune_and_siret_pontivy, insert_financial_ae_for_tag_acv
):
    # DO
    context = {"only": "FINANCIAL_DATA_CP", "id": insert_financial_ae_for_tag_acv.id}
    apply_tags_acv(tag_acv.type, None, json.dumps(context))  # type: ignore

    # ASSERT
    tag_assocation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_acv.id, TagAssociation.financial_ae == insert_financial_ae_for_tag_acv.id
        )
    ).scalar_one_or_none()
    assert tag_assocation is None
    session.execute(delete(TagAssociation))
    session.commit()
    delete_references(session)
