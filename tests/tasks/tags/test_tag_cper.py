import json
import datetime

import pytest

from app.tasks.tags import apply_tags_cper_2015_20
from ..tags import *  # noqa: F403

from app import db
from app.models.financial.FinancialAe import FinancialAe
from app.models.tags.Tags import TagAssociation, Tags


@pytest.fixture(autouse=True)
def tag_cper_15_20(database):
    tags = Tags(**TAG_CPER_15_20)  # noqa: F405
    database.session.add(tags)
    database.session.commit()
    yield tags
    database.session.execute(database.delete(Tags))
    database.session.execute(database.delete(TagAssociation))
    database.session.commit()


@pytest.fixture(autouse=True)
def tag_cper_21_27(database):
    tags = Tags(**TAG_CPER_21_27)  # noqa: F405
    database.session.add(tags)
    database.session.commit()
    yield tags
    database.session.execute(database.delete(Tags))
    database.session.execute(database.delete(TagAssociation))
    database.session.commit()


@pytest.fixture(scope="function")
def insert_two_financial_ae_for_tag_cper_2015_20(database, session):
    ae_2020 = FinancialAe(
        **{
            "annee": 2020,
            "n_ej": "1",
            "n_poste_ej": 1,
            "contrat_etat_region": "CONTRAIT",  # attribut non renseigné
            "programme": "155",  #
            "domaine_fonctionnel": "0380-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "BGOO/DETR",
            "fournisseur_titulaire": 1001465507,
            "localisation_interministerielle": "N35",
            "groupe_marchandise": "groupe",
            "date_modification_ej": datetime.datetime.now(),
            "compte_budgetaire": "co",
        }
    )
    ae_2019 = FinancialAe(
        **{
            "annee": 2019,
            "n_ej": "2",
            "n_poste_ej": 1,
            "contrat_etat_region": "CONTRAT",  # attribut non renseigné
            "programme": "165",  #
            "domaine_fonctionnel": "0380-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "BGOO/DETR",
            "fournisseur_titulaire": 1001465507,
            "localisation_interministerielle": "N35",
            "groupe_marchandise": "groupe",
            "date_modification_ej": datetime.datetime.now(),
            "compte_budgetaire": "co",
        }
    )

    bad_ae_1 = FinancialAe(
        **{
            "annee": 2019,
            "n_ej": "3",
            "n_poste_ej": 1,
            "contrat_etat_region": "#",
            "programme": "165",
            "domaine_fonctionnel": "0380-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "BGOO/DETR",
            "fournisseur_titulaire": 1001465507,
            "localisation_interministerielle": "N35",
            "groupe_marchandise": "groupe",
            "date_modification_ej": datetime.datetime.now(),
            "compte_budgetaire": "co",
        }
    )

    session.add(ae_2020)
    session.add(ae_2019)
    session.add(bad_ae_1)
    session.commit()
    yield [ae_2020, ae_2019]
    session.execute(database.delete(FinancialAe))
    session.commit()


def test_apply_cper_2015_20_no_tag(insert_two_financial_ae_for_tag_cper_2015_20, tag_cper_15_20):
    # DO
    apply_tags_cper_2015_20(tag_cper_15_20.type, "2015-20", None)  # type: ignore

    # assert
    ## on a bien deux associations
    tag_assocations = (
        db.session.execute(db.select(TagAssociation).where(TagAssociation.tag_id == tag_cper_15_20.id))
        .scalars()
        .fetchall()
    )
    assert len(tag_assocations) == 2
    assert (
        (tag_assocations[0].financial_ae == insert_two_financial_ae_for_tag_cper_2015_20[0].id)
        or (tag_assocations[0].financial_ae == insert_two_financial_ae_for_tag_cper_2015_20[1].id)
    ) and (
        (tag_assocations[1].financial_ae == insert_two_financial_ae_for_tag_cper_2015_20[0].id)
        or (tag_assocations[1].financial_ae == insert_two_financial_ae_for_tag_cper_2015_20[1].id)
    )
    assert tag_assocations[0].ademe is None and tag_assocations[1].ademe is None
    assert tag_assocations[0].auto_applied and tag_assocations[1].auto_applied


def test_should_apply_tag_if_context_is_ok(database, tag_cper_15_20, insert_two_financial_ae_for_tag_cper_2015_20):
    # DO
    context = {"only": "FINANCIAL_DATA_AE", "id": insert_two_financial_ae_for_tag_cper_2015_20[0].id}
    apply_tags_cper_2015_20(tag_cper_15_20.type, "2015-20", json.dumps(context))  # type: ignore

    # ASSERT
    tag_assocation: TagAssociation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_cper_15_20.id,
            TagAssociation.financial_ae == insert_two_financial_ae_for_tag_cper_2015_20[0].id,
        )
    ).scalar_one_or_none()
    assert tag_assocation is not None
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_cp is None
    assert tag_assocation.financial_ae == insert_two_financial_ae_for_tag_cper_2015_20[0].id
    assert tag_assocation.auto_applied is True


def test_should_not_apply_tag_if_context_is_not_ok(
    database, tag_cper_15_20, insert_two_financial_ae_for_tag_cper_2015_20
):
    # DO
    context = {"only": "FINANCIAL_DATA_CP", "id": insert_two_financial_ae_for_tag_cper_2015_20[0].id}
    apply_tags_cper_2015_20(tag_cper_15_20.type, "2015-20", json.dumps(context))  # type: ignore

    # ASSERT
    tag_assocation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_cper_15_20.id,
            TagAssociation.financial_ae == insert_two_financial_ae_for_tag_cper_2015_20[0].id,
        )
    ).scalar_one_or_none()
    assert tag_assocation is None
