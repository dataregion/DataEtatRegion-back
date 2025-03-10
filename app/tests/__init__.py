import os
from functools import wraps
from unittest.mock import patch
from pathlib import Path

from app import db  # noqa: F401

from models.entities.common.Tags import Tags
from models.entities.financial.Ademe import Ademe
from models.entities.financial.FinancialAe import FinancialAe
from models.entities.financial.FinancialCp import FinancialCp
from models.entities.financial.France2030 import France2030
from models.entities.refs.CentreCouts import CentreCouts
from models.entities.refs.CodeProgramme import CodeProgramme
from models.entities.refs.DomaineFonctionnel import DomaineFonctionnel
from models.entities.refs.FournisseurTitulaire import FournisseurTitulaire
from models.entities.refs.GroupeMarchandise import GroupeMarchandise
from models.entities.refs.LocalisationInterministerielle import LocalisationInterministerielle
from models.entities.refs.Qpv import Qpv
from models.entities.refs.ReferentielProgrammation import ReferentielProgrammation
from models.entities.refs.Region import Region
from models.entities.refs.Siret import Siret
from models.entities.common.Tags import TagAssociation

from sqlalchemy import delete

TESTS_PATH = Path(os.path.dirname(__file__))


# MOCK du accept_token
def mock_accept_token(*args, **kwargs):
    def wrapper(view_func):
        @wraps(view_func)
        def decorated(*args, **kwargs):
            return view_func(*args, **kwargs)

        return decorated

    return wrapper


patch("authlib.integrations.flask_oauth2.ResourceProtector.acquire_token", mock_accept_token).start()


def delete_references(session):
    # Suppression des objets après le test
    session.execute(delete(TagAssociation))
    session.execute(delete(Tags))
    session.execute(delete(FinancialCp))
    session.execute(delete(FinancialAe))
    session.execute(delete(CodeProgramme))
    session.execute(delete(CentreCouts))
    session.execute(delete(DomaineFonctionnel))
    session.execute(delete(FournisseurTitulaire))
    session.execute(delete(GroupeMarchandise))
    session.execute(delete(LocalisationInterministerielle))
    session.execute(delete(ReferentielProgrammation))
    session.execute(delete(Region))
    session.execute(delete(Ademe))
    session.execute(delete(France2030))
    session.execute(delete(Siret))
    session.execute(delete(Qpv))

    session.commit()
