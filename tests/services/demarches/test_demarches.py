from datetime import datetime
import json
import os
from pathlib import Path
import pytest

from app.models.demarches.demarche import Demarche
from app.models.demarches.donnee import Donnee
from app.models.demarches.dossier import Dossier

from app.models.demarches.section import Section
from app.models.demarches.type import Type

from app.services.demarches.demarches import DemarcheService, DemarcheExistsException


_data = Path(os.path.dirname(__file__)) / "data"


@pytest.fixture(scope="function")
def init_demarche(database):
    with open(_data / "sections.json") as file:
        for section in json.load(file):
            database.session.add(Section(**section))

    with open(_data / "types.json") as file:
        for type in json.load(file):
            database.session.add(Type(**type))

    database.session.add(
        Demarche(
            **{
                "number": "49721",
                "title": "Dotation d'équipement des territoires ruraux (DETR) 2022 - Finistère",
                "centre_couts": "PRFSG04029",
                "domaine_fonctionnel": "0119-01-06",
                "referentiel_programmation": "0119010101A6",
                "state": "publiee",
                "date_creation": datetime.strptime("2021-10-19 10:06:26.000", "%Y-%m-%d %H:%M:%S.%f"),
                "date_import": datetime.strptime("2024-07-29 16:14:09.761", "%Y-%m-%d %H:%M:%S.%f"),
            }
        )
    )

    dossiers: list[Dossier] = [
        {
            "number": "12345",
            "demarche_number": "49721",
            "state": "accepte",
            "siret": "21290243100015",
            "revision_id": "okokok",
            "date_depot": datetime.strptime("2021-10-19 10:06:26.000", "%Y-%m-%d %H:%M:%S.%f"),
            "date_derniere_modification": datetime.strptime("2024-07-30 12:00:00.000", "%Y-%m-%d %H:%M:%S.%f"),
        },
        {
            "number": "67890",
            "demarche_number": "49721",
            "state": "en_instruction",
            "revision_id": "okokok",
            "date_depot": datetime.strptime("2021-10-19 10:06:26.000", "%Y-%m-%d %H:%M:%S.%f"),
            "date_derniere_modification": datetime.strptime("2024-07-30 12:00:00.000", "%Y-%m-%d %H:%M:%S.%f"),
        },
    ]
    for dossier in dossiers:
        database.session.add(Dossier(**dossier))

    with open(_data / "donnees.json") as file:
        for donnee in json.load(file):
            database.session.add(Donnee(**donnee))

    database.session.commit()
    yield dossiers

    database.session.execute(database.delete(Donnee))
    database.session.execute(database.delete(Dossier))
    database.session.execute(database.delete(Demarche))
    database.session.execute(database.delete(Section))
    database.session.execute(database.delete(Type))
    database.session.commit()


def test_demarche_exists_success(init_demarche):
    assert DemarcheService.exists(49721) is True


def test_demarche_exists_fail(init_demarche: Demarche):
    assert DemarcheService.exists(99999) is False


def test_demarche_find_success(init_demarche):
    assert DemarcheService.find(49721) is not None


def test_demarche_find_fail(init_demarche):
    assert DemarcheService.find(99999) is None


def test_demarche_save_success(init_demarche):
    new_dict = {
        "data": {
            "demarche": {
                "title": "Nouvelle démarche",
                "state": "en_instruction",
                "chorusConfiguration": {
                    "centreDeCout": "blabla",
                    "domaineFonctionnel": "blibli",
                    "referentielDeProgrammation": "bloblo",
                },
                "dateCreation": datetime.strptime("2021-10-19 10:06:26.000", "%Y-%m-%d %H:%M:%S.%f"),
                "dateFermeture": datetime.now(),
            }
        }
    }
    new_demarche = DemarcheService.save("99999", new_dict)

    assert int(new_demarche.number) == 99999
    assert DemarcheService.exists(99999) is True


def test_demarche_save_already_exists(init_demarche):
    new_dict = {
        "data": {
            "demarche": {
                "title": "Nouvelle démarche",
                "state": "en_instruction",
                "chorusConfiguration": {
                    "centreDeCout": "blabla",
                    "domaineFonctionnel": "blibli",
                    "referentielDeProgrammation": "bloblo",
                },
                "dateCreation": datetime.strptime("2021-10-19 10:06:26.000", "%Y-%m-%d %H:%M:%S.%f"),
                "dateFermeture": datetime.now(),
            }
        }
    }

    with pytest.raises(DemarcheExistsException, match="La démarche existe déjà en BDD"):
        DemarcheService.save("49721", new_dict)


def test_demarche_update_reconciliation_success(init_demarche):
    DemarcheService.update_reconciliation(49721, {"codeEJ": "0974397398"})
    demarche = DemarcheService.find(49721)

    assert "codeEJ" in demarche.reconciliation
    assert demarche.reconciliation["codeEJ"] == "0974397398"


def test_demarche_update_affichage_success(init_demarche):
    DemarcheService.update_affichage(49721, {"blabla": "bopbop"})
    demarche = DemarcheService.find(49721)

    assert "blabla" in demarche.affichage
    assert demarche.affichage["blabla"] == "bopbop"


def test_demarche_delete_success(init_demarche):
    assert DemarcheService.exists(49721) is True
    demarche: Demarche = DemarcheService.find(49721)
    DemarcheService.delete(demarche)
    assert DemarcheService.exists(49721) is False
