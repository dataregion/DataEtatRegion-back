import datetime

import pytest
from ..tags import *  # noqa: F403

from app.models.financial.FinancialAe import FinancialAe
from app.models.tags.Tags import TagAssociation, Tags
from app.tasks.tags.apply_tags import apply_tags_fonds_vert


@pytest.fixture(scope="function")
def tag_fond_vert(database):
    tags = Tags(**TAG_FOND_VERT)  # noqa: F405
    database.session.add(tags)
    database.session.commit()
    yield tags
    database.session.execute(database.delete(Tags))
    database.session.execute(database.delete(TagAssociation))
    database.session.commit()


@pytest.fixture(scope="function")
def insert_financial_ae_for_tag_fond_vert(database, session):
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


def test_apply_fond_vert_when_no_tag(
    database, insert_financial_ae_for_tag_fond_vert, insert_financial_ae_for_other_tag, tag_fond_vert
):
    # DO
    apply_tags_fonds_vert(tag_fond_vert.type, None, None)  # type: ignore

    # assert
    ## on a bien une association
    tag_assocation: TagAssociation = database.session.execute(
        database.select(TagAssociation).where(TagAssociation.tag_id == tag_fond_vert.id)
    ).scalar_one_or_none()
    assert tag_assocation.ademe is None
    assert (
        tag_assocation.financial_ae == insert_financial_ae_for_tag_fond_vert.id
    )  # il s'agit bien de l'id de l'AE code programme 380
    assert tag_assocation.auto_applied is True


def test_should_apply_tag_if_other_tag_associated(
    database, session, tag_fond_vert, insert_financial_ae_for_tag_fond_vert: FinancialAe
):
    # given
    tags_dummy = Tags(**TAG_DUMMY)  # noqa: F405
    tag_assoc = TagAssociation(**{"financial_ae": insert_financial_ae_for_tag_fond_vert.id, "auto_applied": False})
    tag_assoc.tag = tags_dummy
    session.add(tag_assoc)
    session.commit()

    # DO
    apply_tags_fonds_vert(tag_fond_vert.type, None, None)  # type: ignore

    # ASSERT
    tag_assocations = (
        database.session.execute(
            database.select(TagAssociation).where(
                TagAssociation.financial_ae == insert_financial_ae_for_tag_fond_vert.id
            )
        )
        .scalars()
        .fetchall()
    )

    assert len(tag_assocations) == 2
    assert (tag_assocations[0].tag_id == tags_dummy.id and tag_assocations[1].tag_id == tag_fond_vert.id) or (
        tag_assocations[1].tag_id == tags_dummy.id and tag_assocations[0].tag_id == tag_fond_vert.id
    )

    for t in tag_assocations:
        assert t.financial_ae == insert_financial_ae_for_tag_fond_vert.id


def test_should_not_apply_tag_if_already_present(
    database, session, tag_fond_vert, insert_financial_ae_for_tag_fond_vert: FinancialAe
):
    # given affection du tag fond vert à l'AE
    tag_assoc = TagAssociation(
        **{
            "tag_id": tag_fond_vert.id,
            "financial_ae": insert_financial_ae_for_tag_fond_vert.id,
            "auto_applied": False,
        }
    )
    session.add(tag_assoc)
    session.commit()

    # DO
    apply_tags_fonds_vert(tag_fond_vert.type, None, None)  # type: ignore

    # ASSERT
    tag_assocation = database.session.execute(
        database.select(TagAssociation).where(TagAssociation.tag_id == tag_fond_vert.id)
    ).scalar_one_or_none()
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_ae == insert_financial_ae_for_tag_fond_vert.id
    assert not tag_assocation.auto_applied
