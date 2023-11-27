import datetime
import pytest

from tests.tasks.tags import faked_tag_json

from app import db
from app.models.financial.FinancialAe import FinancialAe
from app.models.tags.Tags import Tags, TagAssociation
from app.tasks.tags.manuels import put_tags_to_ae


@pytest.fixture(autouse=True)
def tag_json(faker):
    json = faked_tag_json(faker)
    return json


@pytest.fixture(autouse=True)
def tag_prettyname(tag_json):
    type = tag_json["type"]
    value = tag_json["value"]

    if value is not None:
        return f"{type}:{value}"
    else:
        return f"{type}"


@pytest.fixture(autouse=True)
def tag(database, tag_json):
    tags = Tags(**tag_json)
    database.session.add(tags)
    database.session.commit()
    yield tags
    database.session.execute(database.delete(Tags))
    database.session.execute(database.delete(TagAssociation))
    database.session.commit()


@pytest.fixture(scope="function")
def insert_two_ae_for_manual_tag(database, session):
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

    session.add(ae_2020)
    session.add(ae_2019)
    session.commit()
    yield [ae_2020, ae_2019]
    session.execute(database.delete(FinancialAe))
    session.commit()


# TODO: démarrer une base postgres pour ces tests
@pytest.mark.skip(reason="sqlite bloque")
def test_ok(insert_two_ae_for_manual_tag, tag, tag_prettyname):
    put_tags_to_ae("2", "1", [tag_prettyname])

    # assert
    ## on a bien une association
    tag_assocations = (
        db.session.execute(db.select(TagAssociation).where(TagAssociation.tag_id == tag.id)).scalars().fetchall()
    )

    assert len(tag_assocations) == 1
