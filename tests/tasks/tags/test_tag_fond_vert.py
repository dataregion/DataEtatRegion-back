import datetime

import pytest
from sqlalchemy import insert
from ..tags import *

from app import db
from app.models.financial.FinancialAe import FinancialAe
from app.models.tags.Tags import TagAssociation, Tags
from app.tasks.tags.apply_tags import apply_tags_fond_vert


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


@pytest.fixture(scope="function")
def insert_financial_ae_for_other_tag(database, session):
    ae = FinancialAe(
        **{
            "annee": 2020,
            "n_ej": "1",
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


def test_apply_fond_vert_when_no_tag(
    insert_financial_ae_for_tag_fond_vert, insert_financial_ae_for_other_tag, insert_tags
):
    # DO
    fond_vert_tag = insert_tags["fond_vert"]
    apply_tags_fond_vert(fond_vert_tag.type, None)

    # assert
    ## on a bien une association
    tag_assocation: TagAssociation = db.session.execute(
        db.select(TagAssociation).where(TagAssociation.tag_id == fond_vert_tag.id)
    ).scalar_one_or_none()
    assert tag_assocation.ademe is None
    assert (
        tag_assocation.financial_ae == insert_financial_ae_for_tag_fond_vert.id
    )  # il s'agit bien de l'id de l'AE code programme 380
    assert tag_assocation.auto_applied == True
