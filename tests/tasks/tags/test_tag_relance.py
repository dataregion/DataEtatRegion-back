import datetime

import pytest

from app.models.refs.code_programme import CodeProgramme
from app.models.refs.theme import Theme
from ..tags import *

from app import db
from app.models.financial.FinancialAe import FinancialAe
from app.models.tags.Tags import TagAssociation, Tags
from app.tasks.tags.apply_tags import apply_tags_relance


@pytest.fixture(autouse=True)
def tag_relance(database):
    tags = Tags(**TAG_RELANCE)
    database.session.add(tags)
    database.session.commit()
    yield tags
    database.session.execute(database.delete(Tags))
    database.session.execute(database.delete(TagAssociation))
    database.session.commit()


@pytest.fixture(scope="function")
def insert_financial_ae_for_tag_relance(database, session):
    programme_t_relance_1 = CodeProgramme(**{"code": "155"})
    programme_t_relance_2 = CodeProgramme(**{"code": "255"})
    programme_t_autre = CodeProgramme(**{"code": "xxx"})
    theme_relance = Theme(**{"label": "Plan de relance"})

    programme_t_relance_1.theme_r = theme_relance
    programme_t_relance_2.theme_r = theme_relance

    ae = FinancialAe(
        **{
            "annee": 2020,
            "n_ej": "1",
            "n_poste_ej": 1,
            "programme": "155",  #
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
    bad_ae = FinancialAe(
        **{
            "annee": 2020,
            "n_ej": "2",
            "n_poste_ej": 2,
            "programme": "xxx",  #
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
    session.add(programme_t_relance_1)
    session.add(programme_t_relance_2)
    session.add(programme_t_autre)
    session.add(ae)
    session.add(bad_ae)
    session.commit()
    yield ae
    session.execute(database.delete(FinancialAe))
    session.execute(database.delete(Theme))
    session.execute(database.delete(CodeProgramme))
    session.commit()


def test_apply_relance_no_tag(insert_financial_ae_for_tag_relance, tag_relance):
    # DO
    apply_tags_relance(tag_relance.type, None)

    # assert
    ## on a bien une association
    tag_assocation: TagAssociation = db.session.execute(
        db.select(TagAssociation).where(TagAssociation.tag_id == tag_relance.id)
    ).scalar_one_or_none()
    assert tag_assocation.ademe is None
    assert (
        tag_assocation.financial_ae == insert_financial_ae_for_tag_relance.id
    )  # il s'agit bien de l'id de l'AE code programme 380
    assert tag_assocation.auto_applied == True


def test_should_not_apply_tag_if_already_present(
    database, session, tag_relance, insert_financial_ae_for_tag_relance: FinancialAe
):
    # given affection du tag relance à l'AE
    tag_assoc = TagAssociation(
        **{
            "tag_id": tag_relance.id,
            "financial_ae": insert_financial_ae_for_tag_relance.id,
            "auto_applied": False,
        }
    )
    session.add(tag_assoc)
    session.commit()
    # check tag bien affecté
    database.session.execute(
        database.select(TagAssociation).where(TagAssociation.tag_id == tag_relance.id)
    ).scalar_one_or_none()

    # DO
    apply_tags_relance(tag_relance.type, None)

    # ASSERT
    tag_assocation = database.session.execute(
        database.select(TagAssociation).where(TagAssociation.tag_id == tag_relance.id)
    ).scalar_one_or_none()
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_ae == insert_financial_ae_for_tag_relance.id
    assert tag_assocation.auto_applied == False
