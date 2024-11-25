import json
import datetime

from models.entities.common.Tags import Tags
import pytest

from models.entities.refs.ReferentielProgrammation import ReferentielProgrammation
from tests import delete_references
from tests.tasks.tags.test_tag_acv import add_references
from ..tags import *  # noqa: F403

from app import db
from models.entities.financial.FinancialAe import FinancialAe
from models.entities.common.Tags import TagAssociation
from app.tasks.tags.apply_tags import apply_tags_detr


@pytest.fixture(autouse=True)
def tag_detr(database):
    tags = Tags(**TAG_DETR)  # noqa: F405
    database.session.add(tags)
    database.session.commit()
    yield tags
    database.session.execute(database.delete(Tags))
    database.session.execute(database.delete(TagAssociation))
    database.session.commit()


@pytest.fixture(scope="function")
def insert_two_financial_ae_for_tag_detr(database, session):
    ref_prog_detr = ReferentielProgrammation(**{"code": "code_detr", "label": "DETR"})

    ae_1 = FinancialAe(
        **{
            "annee": 2020,
            "n_ej": "1",
            "n_poste_ej": 1,
            "programme": "155",  #
            "domaine_fonctionnel": "0380-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "code_detr",
            "fournisseur_titulaire": "1001465507",
            "localisation_interministerielle": "N35",
            "groupe_marchandise": "groupe",
            "date_modification_ej": datetime.datetime.now(),
            "compte_budgetaire": "co",
            "siret": "851296632000171",
            "data_source": "REGION",
        }
    )
    ae_2 = FinancialAe(
        **{
            "annee": 2020,
            "n_ej": "2",
            "n_poste_ej": 1,
            "programme": "165",  #
            "domaine_fonctionnel": "0380-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "code_detr",
            "fournisseur_titulaire": "1001465507",
            "localisation_interministerielle": "N35",
            "groupe_marchandise": "groupe",
            "date_modification_ej": datetime.datetime.now(),
            "compte_budgetaire": "co",
            "siret": "851296632000171",
            "data_source": "REGION",
        }
    )
    bad_ae = FinancialAe(
        **{
            "annee": 2020,
            "n_ej": "3",
            "n_poste_ej": 2,
            "programme": "xxx",  #
            "domaine_fonctionnel": "0380-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "dddd",
            "fournisseur_titulaire": "1001465507",
            "localisation_interministerielle": "N35",
            "groupe_marchandise": "groupe",
            "date_modification_ej": datetime.datetime.now(),
            "compte_budgetaire": "co",
            "siret": "851296632000171",
            "data_source": "REGION",
        }
    )
    session.add(ref_prog_detr)
    add_references(ae_1, session, region="53")
    add_references(ae_2, session, region="53")
    add_references(bad_ae, session, region="53")
    session.add(ae_1)
    session.add(ae_2)
    session.add(bad_ae)
    session.commit()
    yield [ae_1, ae_2]
    delete_references(session)  # noqa: F405
    session.execute(database.delete(FinancialAe))
    session.execute(database.delete(ReferentielProgrammation))
    session.commit()


def test_apply_detr_no_tag(insert_two_financial_ae_for_tag_detr, tag_detr):
    # DO
    apply_tags_detr(tag_detr.type, None, None)  # type: ignore

    # assert
    ## on a bien une association
    tag_assocations = (
        db.session.execute(db.select(TagAssociation).where(TagAssociation.tag_id == tag_detr.id)).scalars().fetchall()
    )
    assert len(tag_assocations) == 2
    assert (
        (tag_assocations[0].financial_ae == insert_two_financial_ae_for_tag_detr[0].id)
        or (tag_assocations[0].financial_ae == insert_two_financial_ae_for_tag_detr[1].id)
    ) and (
        (tag_assocations[1].financial_ae == insert_two_financial_ae_for_tag_detr[0].id)
        or (tag_assocations[1].financial_ae == insert_two_financial_ae_for_tag_detr[1].id)
    )
    assert tag_assocations[0].ademe is None and tag_assocations[1].ademe is None
    assert tag_assocations[0].auto_applied and tag_assocations[1].auto_applied


def test_should_not_apply_tag_if_already_present(database, session, tag_detr, insert_two_financial_ae_for_tag_detr):
    # given affection du tag relance à l'AE
    tag_assoc = TagAssociation(
        **{
            "tag_id": tag_detr.id,
            "financial_ae": insert_two_financial_ae_for_tag_detr[0].id,
            "auto_applied": False,
        }
    )
    session.add(tag_assoc)
    session.commit()
    # check tag bien affecté
    database.session.execute(
        database.select(TagAssociation)
        .where(TagAssociation.tag_id == tag_detr.id)
        .where(TagAssociation.financial_ae == insert_two_financial_ae_for_tag_detr[0].id)
    ).scalar_one_or_none()

    # DO
    apply_tags_detr(tag_detr.type, None, None)  # type: ignore

    # ASSERT
    tag_assocation = database.session.execute(
        database.select(TagAssociation)
        .where(TagAssociation.tag_id == tag_detr.id)
        .where(TagAssociation.financial_ae == insert_two_financial_ae_for_tag_detr[0].id)
    ).scalar_one_or_none()
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_ae == insert_two_financial_ae_for_tag_detr[0].id
    assert not tag_assocation.auto_applied


def test_should_apply_tag_if_context_is_ok(database, tag_detr, insert_two_financial_ae_for_tag_detr):
    # DO
    context = {"only": "FINANCIAL_DATA_AE", "id": insert_two_financial_ae_for_tag_detr[0].id}
    apply_tags_detr(tag_detr.type, None, json.dumps(context))  # type: ignore

    # ASSERT
    tag_assocation: TagAssociation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_detr.id,
            TagAssociation.financial_ae == insert_two_financial_ae_for_tag_detr[0].id,
        )
    ).scalar_one_or_none()
    assert tag_assocation is not None
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_cp is None
    assert tag_assocation.financial_ae == insert_two_financial_ae_for_tag_detr[0].id
    assert tag_assocation.auto_applied is True


def test_should_not_apply_tag_if_context_is_not_ok(database, tag_detr, insert_two_financial_ae_for_tag_detr):
    # DO
    context = {"only": "FINANCIAL_DATA_CP", "id": insert_two_financial_ae_for_tag_detr[0].id}
    apply_tags_detr(tag_detr.type, None, json.dumps(context))  # type: ignore

    # ASSERT
    tag_assocation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_detr.id,
            TagAssociation.financial_ae == insert_two_financial_ae_for_tag_detr[0].id,
        )
    ).scalar_one_or_none()
    assert tag_assocation is None
