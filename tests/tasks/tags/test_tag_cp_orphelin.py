import json
import pytest
from app.models.financial.FinancialCp import FinancialCp
from app.models.tags.Tags import Tags, TagAssociation
from app.tasks.tags.apply_tags import apply_tags_cp_orphelin

from tests.tasks.tags import TAG_CP_SANS_AE


@pytest.fixture(scope="function")
def tag_cp_orphan(database):
    tags = Tags(**TAG_CP_SANS_AE)  # type: ignore
    database.session.add(tags)
    database.session.commit()
    yield tags
    database.session.execute(database.delete(Tags))
    database.session.execute(database.delete(TagAssociation))
    database.session.commit()


@pytest.fixture(scope="function")
def cp_orphelin(database, session):
    """Insère un CP sans AE rattaché (avec ou sans n_ej)"""
    cp = FinancialCp(
        line_chorus={
            "annee": 2020,
            "n_ej": "1",
            "n_poste_ej": 1,
            "n_dp": "numero dp",
            "programme": "380",
            "domaine_fonctionnel": "0380-01-01",
            "centre_couts": "BG00\\/DREETS0035",
            "referentiel_programmation": "BG00\\/010300000108",
            "fournisseur_titulaire": 1001465507,
            "localisation_interministerielle": "N35",
            "fournisseur_paye": "1000373509",
            "groupe_marchandise": "groupe",
            "compte_budgetaire": "co",
        },
        annee=2021,
        source_region="53",
    )

    session.add(cp)
    session.commit()
    yield cp
    session.execute(database.delete(FinancialCp))
    session.commit()


def test_apply_cp_orphelin(
    database,
    cp_orphelin,
    tag_cp_orphan,
):
    # DO
    apply_tags_cp_orphelin(tag_cp_orphan.type, None, None)  # type: ignore

    # assert
    ## On a bien une association
    tag_assocation: TagAssociation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_cp_orphan.id, TagAssociation.financial_cp == cp_orphelin.id
        )
    ).scalar_one_or_none()
    assert tag_assocation.financial_cp == cp_orphelin.id
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_ae is None


def test_should_apply_tag_if_context_is_ok(database, tag_cp_orphan, cp_orphelin):
    # DO
    context = {"only": "FINANCIAL_DATA_CP", "id": cp_orphelin.id}
    apply_tags_cp_orphelin(tag_cp_orphan.type, None, json.dumps(context))  # type: ignore

    # ASSERT
    tag_assocation: TagAssociation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_cp_orphan.id, TagAssociation.financial_cp == cp_orphelin.id
        )
    ).scalar_one_or_none()
    assert tag_assocation is not None
    assert tag_assocation.ademe is None
    assert tag_assocation.financial_cp == cp_orphelin.id
    assert tag_assocation.financial_ae is None
    assert tag_assocation.auto_applied is True


def test_should_not_apply_tag_if_context_is_not_ok(database, tag_cp_orphan, cp_orphelin):
    # DO
    context = {"only": "FINANCIAL_DATA_AE", "id": cp_orphelin.id}
    apply_tags_cp_orphelin(tag_cp_orphan.type, None, json.dumps(context))  # type: ignore

    # ASSERT
    tag_assocation = database.session.execute(
        database.select(TagAssociation).where(
            TagAssociation.tag_id == tag_cp_orphan.id, TagAssociation.financial_cp == cp_orphelin.id
        )
    ).scalar_one_or_none()
    assert tag_assocation is None
