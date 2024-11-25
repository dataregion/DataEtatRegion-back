import pytest


__all__ = ("init_ref_ministeres_themes", "insert_centre_couts")


from models.entities.refs.CodeProgramme import CodeProgramme
from models.entities.refs.CentreCouts import CentreCouts
from models.entities.refs.Ministere import Ministere
from models.entities.refs.Theme import Theme

ministere01 = {"code": "MIN01", "label": "label MIN01groscccccccc"}
ministere02 = {"code": "MIN02", "label": "label MIN02"}

theme01 = {"id": 1, "label": "theme 01"}
theme02 = {"id": 2, "label": "theme 02"}


@pytest.fixture(scope="function")
def init_ref_ministeres_themes(session):
    data = []
    session.add(Ministere(**ministere01))
    session.add(Ministere(**ministere02))
    session.add(Theme(**theme01))
    session.add(Theme(**theme02))

    for i in range(10):
        bop = {
            "code": f"BOP{i + 1}",
            "code_ministere": "MIN01" if i % 5 == 0 else "MIN02",
            "theme": 1 if i % 2 == 0 else 2,
            "label": f"label programme {i + 1}",
            "description": f"description du bop {i + 1}",
        }
        session.add(CodeProgramme(**bop))
        data.append(bop)
    return data


@pytest.fixture(scope="module")
def insert_centre_couts(database):
    # on utilise database fixture pour insérer une seule fois le referentiel.
    data = []
    for i in range(20):
        cc = {
            "code": f"code{i + 1}",
            "label": f"Test code{i * 10}",
            "description": "description du code",
            "code_postal": f"354{i + 1}",
            "ville": f"Rennes {i + 1}",
        }
        database.session.add(CentreCouts(**cc))
        data.append(cc)
    database.session.commit()
    yield data
    database.session.execute(database.delete(CentreCouts))
