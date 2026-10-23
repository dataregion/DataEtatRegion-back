import re
from datetime import date
from pathlib import Path

import pytest
from sqlalchemy import select

from models.entities.refs.Commune import Commune


def _get_commune(session, code: str) -> Commune:
    session.expire_all()
    return session.execute(select(Commune).where(Commune.code == code)).scalar_one()


def test_import_file_pvd_from_website(session, clean_communes, mock_download):
    # XXX: important de delayer l'import pour attendre que la fixture prefect soit appliquée
    # avant la lecture du flow.
    from batches.prefect.import_file_communes import import_file_pvd_from_website

    session.add_all(
        [
            Commune(code="56061", label_commune="La Gacilly", code_departement="56", is_pvd=False),
            Commune(code="29284", label_commune="Treffiagat", code_departement="29", is_pvd=False),
            Commune(code="99999", label_commune="Hors fichier", is_pvd=True, date_pvd=date(2020, 1, 1)),
        ]
    )
    session.commit()
    mock_download("pvd.csv")

    archived = Path(import_file_pvd_from_website("http://fake-url/pvd.csv"))

    assert archived.exists()
    assert archived.parent.name == "communes"
    assert re.fullmatch(r"pvd_\d{14}\.csv", archived.name)

    commune = _get_commune(session, "56061")
    assert commune.is_pvd is True
    assert commune.date_pvd == date(2021, 7, 9)

    # Commune présente dans le fichier sans date de signature
    commune_sans_date = _get_commune(session, "29284")
    assert commune_sans_date.is_pvd is True
    assert commune_sans_date.date_pvd is None

    # Les communes absentes du fichier perdent leur statut PVD
    commune_hors_fichier = _get_commune(session, "99999")
    assert commune_hors_fichier.is_pvd is False
    assert commune_hors_fichier.date_pvd is None


def test_import_file_acv_from_website(session, clean_communes, mock_download):
    # XXX: important de delayer l'import pour attendre que la fixture prefect soit appliquée
    # avant la lecture du flow.
    from batches.prefect.import_file_communes import import_file_acv_from_website

    session.add_all(
        [
            Commune(code="35288", label_commune="Saint-Malo", code_departement="35", is_acv=False),
            Commune(code="67462", label_commune="Sélestat", code_departement="67", is_acv=False),
            Commune(code="99999", label_commune="Hors fichier", is_acv=True, date_acv=date(2020, 1, 1)),
        ]
    )
    session.commit()
    mock_download("acv.csv")

    archived = Path(import_file_acv_from_website("http://fake-url/acv.csv"))

    assert archived.exists()
    assert archived.parent.name == "communes"
    assert re.fullmatch(r"acv_\d{14}\.csv", archived.name)

    commune = _get_commune(session, "35288")
    assert commune.is_acv is True
    assert commune.date_acv == date(2018, 9, 21)

    # Commune présente dans le fichier sans date de signature
    commune_sans_date = _get_commune(session, "67462")
    assert commune_sans_date.is_acv is True
    assert commune_sans_date.date_acv is None

    # Les communes absentes du fichier perdent leur statut ACV
    commune_hors_fichier = _get_commune(session, "99999")
    assert commune_hors_fichier.is_acv is False
    assert commune_hors_fichier.date_acv is None


def test_import_file_pvd_from_website_en_erreur(session, clean_communes, mock_download, tmp_path):
    # XXX: important de delayer l'import pour attendre que la fixture prefect soit appliquée
    # avant la lecture du flow.
    from batches.prefect.import_file_communes import import_file_pvd_from_website

    session.add(Commune(code="56061", label_commune="La Gacilly", is_pvd=True, date_pvd=date(2020, 1, 1)))
    session.commit()
    mock_download("pvd_date_invalide.csv")

    with pytest.raises(ValueError):
        import_file_pvd_from_website("http://fake-url/pvd.csv")

    # Le fichier téléchargé est supprimé et rien n'est archivé
    assert not (tmp_path / "pvd_date_invalide.csv").exists()
    assert not (tmp_path / "imports" / "communes").exists()

    # La remise à zéro est annulée avec le reste de la transaction
    commune = _get_commune(session, "56061")
    assert commune.is_pvd is True
    assert commune.date_pvd == date(2020, 1, 1)
