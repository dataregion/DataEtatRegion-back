import json
import datetime

from models.entities.common.Tags import Tags
import pytest

from models.entities.refs.Commune import Commune
from models.entities.refs.Siret import Siret
from tests import delete_references
from tests.tasks.tags.test_tag_acv import add_references
from ..tags import *  # noqa: F403

from models.entities.financial.FinancialAe import FinancialAe
from models.entities.common.Tags import TagAssociation
from app.tasks.tags.apply_tags import apply_tags_pvd


@pytest.fixture(scope="function")
def tag_pvd(database):
    tags = Tags(**TAG_PVD)  # noqa: F405
    database.session.add(tags)
    database.session.commit()
    yield tags
    database.session.execute(database.delete(Tags))
    database.session.execute(database.delete(TagAssociation))
    database.session.commit()


@pytest.fixture(scope="function")
def add_commune_cancale(database):
    commune = Commune(
        **{
            "id": "111",
            "code": "35049",
            "label_commune": "Cancale",
            "code_departement": "35",
            "is_pvd": True,
            "date_pvd": None,
        }
    )
    database.session.add(commune)
    database.session.commit()
    yield commune
    database.session.execute(database.delete(Commune))
    database.session.commit()


@pytest.fixture(scope="function")
def add_siret_cancale(database):
    siret = Siret(**{"code": "90933627300000", "code_commune": "35049", "denomination": "TEST"})
    database.session.add(siret)
    database.session.commit()
    yield siret
    database.session.execute(database.delete(Siret))
    database.session.commit()


@pytest.fixture(scope="function")
def insert_financial_ae_for_tag_pvd(database, session):
    no_siret = "20006628000070"
    code_commune = "code_commune_pvd"

    commune_pvd = Commune()
    commune_pvd.code = code_commune
    commune_pvd.is_pvd = True

    siret = Siret()
    siret.code = no_siret
    siret.code_commune = code_commune

    ae = FinancialAe(
        **{
            "annee": 2020,
            "n_ej": "1",
            "n_poste_ej": 1,
            "programme": "380",
            "domaine_fonctionnel": "0380-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "BG00\\/010300000108",
            "fournisseur_titulaire": "1001465507",
            "siret": no_siret,
            "localisation_interministerielle": "N35",
            "groupe_marchandise": "groupe",
            "date_modification_ej": datetime.datetime.now(),
            "compte_budgetaire": "co",
            "data_source": "REGION",
        }
    )
    session.add(commune_pvd)
    session.add(siret)
    add_references(ae, session, region="53")
    session.add(ae)
    session.commit()
    yield ae
    delete_references(session)  # noqa: F405
    session.execute(database.delete(FinancialAe))
    session.execute(database.delete(Siret))
    session.execute(database.delete(Commune))
    session.commit()


@pytest.fixture(scope="function")
def insert_financial_ae_for_other_tag(database, session):
    ae = FinancialAe(
        **{
            "annee": 2020,
            "n_ej": "2",
            "n_poste_ej": 1,
            "programme": "200",
            "domaine_fonctionnel": "0380-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "BG00\\/010300000108",
            "fournisseur_titulaire": "1001465507",
            "localisation_interministerielle": "N35",
            "siret": "90933627300000",
            "groupe_marchandise": "groupe",
            "date_modification_ej": datetime.datetime.now(),
            "compte_budgetaire": "co",
            "data_source": "REGION",
        }
    )
    add_references(ae, session, region="53")
    session.add(ae)
    session.commit()
    yield ae
    delete_references(session)
    session.execute(database.delete(FinancialAe))
    session.commit()


def test_apply_pvd_when_no_tag(
    database,
    insert_financial_ae_for_tag_pvd,
    insert_financial_ae_for_other_tag,
    tag_pvd,
):
    # DO
    apply_tags_pvd(tag_pvd.type, None, None)  # type: ignore

    # assert
    ## on a bien une association
    tag_assocation: TagAssociation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_pvd.id, TagAssociation.financial_ae == insert_financial_ae_for_tag_pvd.id
        )
    ).scalar_one_or_none()
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_ae == insert_financial_ae_for_tag_pvd.id
    assert tag_assocation.auto_applied is True


def test_should_apply_tag_if_other_tag_associated(
    database, session, tag_pvd, insert_financial_ae_for_tag_pvd: FinancialAe
):
    # given
    tags_dummy = Tags(**TAG_DUMMY)  # noqa: F405
    tag_assoc = TagAssociation(**{"financial_ae": insert_financial_ae_for_tag_pvd.id, "auto_applied": False})
    tag_assoc.tag = tags_dummy
    session.add(tag_assoc)
    session.commit()

    # DO
    apply_tags_pvd(tag_pvd.type, None, None)  # type: ignore

    # ASSERT
    tag_assocations = (
        database.session.execute(
            database.select(TagAssociation).where(TagAssociation.financial_ae == insert_financial_ae_for_tag_pvd.id)
        )
        .scalars()
        .fetchall()
    )

    assert len(tag_assocations) == 2
    assert (tag_assocations[0].tag_id == tags_dummy.id and tag_assocations[1].tag_id == tag_pvd.id) or (
        tag_assocations[1].tag_id == tags_dummy.id and tag_assocations[0].tag_id == tag_pvd.id
    )

    for t in tag_assocations:
        assert t.financial_ae == insert_financial_ae_for_tag_pvd.id


def test_should_not_apply_tag_if_already_present(
    database, session, tag_pvd, insert_financial_ae_for_tag_pvd: FinancialAe
):
    # given affection du tag pvd à l'AE
    tag_assoc = TagAssociation(
        **{
            "tag_id": tag_pvd.id,
            "financial_ae": insert_financial_ae_for_tag_pvd.id,
            "auto_applied": False,
        }
    )
    session.add(tag_assoc)
    session.commit()

    # DO
    apply_tags_pvd(tag_pvd.type, None, None)  # type: ignore

    # ASSERT
    tag_assocation = database.session.execute(
        database.select(TagAssociation).where(TagAssociation.tag_id == tag_pvd.id)
    ).scalar_one_or_none()
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_ae == insert_financial_ae_for_tag_pvd.id
    assert not tag_assocation.auto_applied


def test_should_apply_tag_if_context_is_ok(
    database, tag_pvd, add_commune_cancale, add_siret_cancale, insert_financial_ae_for_tag_pvd
):
    # DO
    context = {"only": "FINANCIAL_DATA_AE", "id": insert_financial_ae_for_tag_pvd.id}
    apply_tags_pvd(tag_pvd.type, None, json.dumps(context))  # type: ignore

    # ASSERT
    tag_assocation: TagAssociation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_pvd.id, TagAssociation.financial_ae == insert_financial_ae_for_tag_pvd.id
        )
    ).scalar_one_or_none()
    assert tag_assocation is not None
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_cp is None
    assert tag_assocation.financial_ae == insert_financial_ae_for_tag_pvd.id
    assert tag_assocation.auto_applied is True


def test_should_not_apply_tag_if_context_is_not_ok(
    database, tag_pvd, add_commune_cancale, add_siret_cancale, insert_financial_ae_for_tag_pvd
):
    # DO
    context = {"only": "FINANCIAL_DATA_CP", "id": insert_financial_ae_for_tag_pvd.id}
    apply_tags_pvd(tag_pvd.type, None, json.dumps(context))  # type: ignore

    # ASSERT
    tag_assocation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_pvd.id, TagAssociation.financial_ae == insert_financial_ae_for_tag_pvd.id
        )
    ).scalar_one_or_none()
    assert tag_assocation is None
