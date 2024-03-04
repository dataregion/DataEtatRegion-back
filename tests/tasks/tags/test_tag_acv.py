import json
import datetime

import pytest

from app.models.refs.commune import Commune
from app.models.refs.siret import Siret
from ..tags import *  # noqa: F403

from app.models.financial.FinancialAe import FinancialAe
from app.models.tags.Tags import TagAssociation, Tags
from app.tasks.tags.apply_tags import apply_tags_acv


@pytest.fixture(scope="function")
def tag_acv(database):
    tags = Tags(**TAG_ACV)  # noqa: F405
    database.session.add(tags)
    database.session.commit()
    yield tags
    database.session.execute(database.delete(Tags))
    database.session.execute(database.delete(TagAssociation))
    database.session.commit()


@pytest.fixture(scope="function")
def add_commune_pontivy(database):
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
    siret = Siret(**{"code": "90933627300000", "code_commune": "56178", "denomination": "TEST"})
    database.session.add(siret)
    database.session.commit()
    yield siret
    database.session.execute(database.delete(Siret))
    database.session.commit()


@pytest.fixture(scope="function")
def insert_financial_ae_for_tag_acv(database, session):
    ae = FinancialAe(
        **{
            "annee": 2020,
            "n_ej": "1",
            "n_poste_ej": 1,
            "programme": "380",
            "domaine_fonctionnel": "0380-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "BG00\\/010300000108",
            "fournisseur_titulaire": 1001465507,
            "siret": "90933627300000",
            "localisation_interministerielle": "N35",
            "groupe_marchandise": "groupe",
            "date_modification_ej": datetime.datetime.now(),
            "compte_budgetaire": "co",
        }
    )
    session.add(ae)
    session.commit()
    yield ae
    session.execute(database.delete(FinancialAe))
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
            "fournisseur_titulaire": 1001465507,
            "localisation_interministerielle": "N35",
            "siret": "90933627300000",
            "groupe_marchandise": "groupe",
            "date_modification_ej": datetime.datetime.now(),
            "compte_budgetaire": "co",
        }
    )
    session.add(ae)
    session.commit()
    yield ae
    session.execute(database.delete(FinancialAe))
    session.commit()


def test_apply_acv_when_no_tag(
    database,
    insert_financial_ae_for_tag_acv,
    insert_financial_ae_for_other_tag,
    add_commune_pontivy,
    add_siret_pontivy,
    tag_acv,
):
    # DO
    apply_tags_acv(tag_acv.type, None, None)  # type: ignore

    # assert
    ## on a bien une association
    tag_assocation: TagAssociation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_acv.id, TagAssociation.financial_ae == insert_financial_ae_for_tag_acv.id
        )
    ).scalar_one_or_none()
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_ae == insert_financial_ae_for_tag_acv.id
    assert tag_assocation.auto_applied is True


def test_should_apply_tag_if_other_tag_associated(
    database, session, tag_acv, add_commune_pontivy, add_siret_pontivy, insert_financial_ae_for_tag_acv: FinancialAe
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
    tag_assocations = (
        database.session.execute(
            database.select(TagAssociation).where(TagAssociation.financial_ae == insert_financial_ae_for_tag_acv.id)
        )
        .scalars()
        .fetchall()
    )

    assert len(tag_assocations) == 2
    assert (tag_assocations[0].tag_id == tags_dummy.id and tag_assocations[1].tag_id == tag_acv.id) or (
        tag_assocations[1].tag_id == tags_dummy.id and tag_assocations[0].tag_id == tag_acv.id
    )

    for t in tag_assocations:
        assert t.financial_ae == insert_financial_ae_for_tag_acv.id


def test_should_not_apply_tag_if_already_present(database, session, tag_acv, insert_financial_ae_for_tag_acv):
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
    database, tag_acv, add_commune_pontivy, add_siret_pontivy, insert_financial_ae_for_tag_acv
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
    database, tag_acv, add_commune_pontivy, add_siret_pontivy, insert_financial_ae_for_tag_acv
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
