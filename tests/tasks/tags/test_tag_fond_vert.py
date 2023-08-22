import datetime

import pytest
from sqlalchemy import insert
from ..tags import *

from app import db
from app.models.financial.FinancialAe import FinancialAe
from app.models.tags.Tags import TagAssociation
from app.tasks.tags.apply_tags import apply_tags_fond_vert


@pytest.fixture(scope="module")
def financial_ae_with_no_tag(test_db):
    data = [
        {
            "id": 1,
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
    ]
    data = test_db.session.execute(db.select(FinancialAe)).all()

    test_db.session.execute(insert(FinancialAe), data)
    test_db.session.commit()


def test_apply_fond_vert_when_no_tag(financial_ae_with_no_tag, insert_tags):
    # DO
    apply_tags_fond_vert(1)



    data = db.session.execute(db.select(TagAssociation).where(TagAssociation.tag_id == 1)).all()
    print(data)


