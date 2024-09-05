import os
from functools import wraps
from unittest.mock import patch
from pathlib import Path

from app.models.financial.Ademe import Ademe
from app.models.financial.FinancialAe import FinancialAe
from app.models.financial.FinancialCp import FinancialCp
from app.models.financial.France2030 import France2030
from app.models.refs.centre_couts import CentreCouts
from app.models.refs.code_programme import CodeProgramme
from app.models.refs.domaine_fonctionnel import DomaineFonctionnel
from app.models.refs.fournisseur_titulaire import FournisseurTitulaire
from app.models.refs.groupe_marchandise import GroupeMarchandise
from app.models.refs.localisation_interministerielle import LocalisationInterministerielle
from app.models.refs.referentiel_programmation import ReferentielProgrammation
from app.models.refs.region import Region
from app.models.refs.siret import Siret
from app.models.tags.Tags import TagAssociation, Tags

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


patch("flask_pyoidc.OIDCAuthentication.token_auth", mock_accept_token).start()


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

    session.commit()
