import json
import os
from datetime import datetime
from pathlib import Path

import pytest

from models.entities.demarches.Demarche import Demarche
from models.entities.demarches.Donnee import Donnee
from models.entities.demarches.Dossier import Dossier
from models.entities.demarches.Section import Section
from models.entities.demarches.Type import Type
from app.services.demarches.dossiers import DossierExistsException, DossierService

_data = Path(os.path.dirname(__file__)) / "data"


@pytest.fixture(scope="function")
def init_dossiers(database):
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


def test_dossiers_find_by_demarche(init_dossiers):
    assert len(DossierService.find_by_demarche(49721, "accepte")) == 1
    assert len(DossierService.find_by_demarche(49721, "en_instruction")) == 1
    assert len(DossierService.find_by_demarche(99999, "accepte")) == 0


def test_dossiers_get_donnees(init_dossiers):
    dossier: Dossier = {
        "number": 12345,
        "state": "accepte",
        "demarche": {
            "revision": {
                "id": "okokok",
                "champDescriptors": [{"label": "Email du référent", "__typename": "EmailChampDescriptor"}],
                "annotationDescriptors": [{"label": "EJ", "__typename": "EngagementJuridiqueChampDescriptor"}],
            },
        },
        "demandeur": {"siret": "my_big_siret"},
        "dateDepot": datetime.strptime("2021-10-19 10:06:26.000", "%Y-%m-%d %H:%M:%S.%f"),
        "dateDernierModification": datetime.now(),
    }

    assert (
        len(
            DossierService.get_donnees(
                dossier,
                49721,
                [
                    {
                        "id": "okokok",
                        "champDescriptors": [
                            {"id": "a", "label": "Email du référent", "__typename": "EmailChampDescriptor"}
                        ],
                        "annotationDescriptors": [
                            {"id": "b", "label": "EJ", "__typename": "EngagementJuridiqueChampDescriptor"}
                        ],
                    }
                ],
            )
        )
        == 2
    )


def test_demarche_save_success(init_dossiers):
    new_dict = {
        "number": 98765,
        "state": "refuse",
        "demarche": {
            "revision": {"id": "kokoko"},
        },
        "demandeur": {"siret": "my_big_siret"},
        "dateDepot": datetime.strptime("2021-10-19 10:06:26.000", "%Y-%m-%d %H:%M:%S.%f"),
        "dateDerniereModification": datetime.now(),
    }
    DossierService.save("49721", new_dict)

    assert len(DossierService.find_by_demarche(49721, "accepte")) == 1
    assert len(DossierService.find_by_demarche(49721, "en_instruction")) == 1
    assert len(DossierService.find_by_demarche(49721, "refuse")) == 1


def test_demarche_save_already_exists(init_dossiers):
    new_dict = {
        "number": 12345,
        "state": "refuse",
        "demarche": {
            "revision": {
                "id": "okokok",
                "champDescriptors": [{"label": "Email du référent", "__typename": "EmailChampDescriptor"}],
                "annotationDescriptors": [{"label": "EJ", "__typename": "EngagementJuridiqueChampDescriptor"}],
            },
        },
        "demandeur": {"siret": "my_big_siret"},
        "dateDepot": datetime.strptime("2021-10-19 10:06:26.000", "%Y-%m-%d %H:%M:%S.%f"),
        "dateDerniereModification": datetime.now(),
    }

    with pytest.raises(DossierExistsException, match="Le dossier existe déjà en BDD"):
        DossierService.save("49721", new_dict)
