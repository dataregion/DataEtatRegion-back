from unittest.mock import MagicMock
import contextlib
import logging

from api_entreprise import ApiError
from api_entreprise.models.errors import ApiErrorResponse
from api_entreprise.models.errors import ApiError as ApiErrorModel

from models.entities.refs.Siret import Siret  # noqa: E402
from models.entities.refs.Commune import Commune  # noqa: E402
from models.entities.refs.CategorieJuridique import CategorieJuridique
from sqlalchemy import text  # noqa: E402

from batches.database import get_session_main

import pytest


# ──────────────────────────────────────────────
# Fixtures
# ──────────────────────────────────────────────
@pytest.fixture(autouse=True, scope="function")
def truncate_test_data(session):
    yield
    try:
        session.execute(text("TRUNCATE TABLE ref_siret RESTART IDENTITY CASCADE;"))
        session.execute(text("TRUNCATE TABLE ref_commune RESTART IDENTITY CASCADE;"))
        session.execute(text("TRUNCATE TABLE ref_categorie_juridique RESTART IDENTITY CASCADE;"))
        session.commit()
    except Exception as e:
        session.rollback()
        raise e


@pytest.fixture
def session(test_db):
    gen = get_session_main()
    session = next(gen)
    try:
        yield session
    finally:
        try:
            next(gen)
        except StopIteration:
            pass


@pytest.fixture(autouse=True)
def prepare_update_siret_module_for_tests(session, monkeypatch):
    """Patch session_scope dans le module update_siret pour utiliser la session de test."""
    import batches.prefect.update_siret as update_siret_mod

    @contextlib.contextmanager
    def _session_scope_override():
        yield session
        session.flush()

    # Patch session_scope
    monkeypatch.setattr(update_siret_mod, "session_scope", _session_scope_override)

    # Patch _get_logger pour retourner un logger Python standard
    def _get_test_logger():
        return logging.getLogger("test_update_siret")

    monkeypatch.setattr(update_siret_mod, "_get_logger", _get_test_logger)


@pytest.fixture
def ref_commune(session):
    """Insère la commune de test pour satisfaire les FK."""
    commune = Commune(code=_TEST_CODE_COMMUNE, label_commune="Rennes")
    session.add(commune)
    session.flush()
    yield commune


@pytest.fixture
def ref_categorie_juridique(session):
    """Insère la catégorie juridique de test pour satisfaire les FK."""
    cat = CategorieJuridique(code=_TEST_CATEGORIE_JURIDIQUE, type="Collectivité", label="Commune")
    session.add(cat)
    session.flush()
    yield cat


@pytest.fixture
def ref_dependants(ref_commune, ref_categorie_juridique):
    """Fixture combinée qui insère les données dépendantes nécessaires au siret."""
    yield


@pytest.fixture
def sample_sirets(session):
    """Insère quelques SIRETs de test en base."""
    codes = ["12345678901234", "98765432109876", "11111111111111"]
    sirets = []
    for code in codes:
        siret = Siret(code=code)
        session.add(siret)
        sirets.append(siret)
    session.flush()
    yield sirets


@pytest.fixture
def many_sirets(session):
    """Insère 10 SIRETs pour tester la condition d'arrêt."""
    sirets = []
    for i in range(10):
        code = f"{i:014d}"
        siret = Siret(code=code)
        session.add(siret)
        sirets.append(siret)
    session.flush()
    yield sirets


# ──────────────────────────────────────────────
# Helpers / Mocks
# ──────────────────────────────────────────────

# Valeurs par défaut pour les FK qui doivent exister en DB


_TEST_CODE_COMMUNE = "35238"
_TEST_CATEGORIE_JURIDIQUE = "7210"


def _make_mock_etablissement(
    code_commune: str | None = _TEST_CODE_COMMUNE,
    categorie_juridique: str | None = _TEST_CATEGORIE_JURIDIQUE,
    raison_sociale: str = "MAIRIE DE RENNES",
    adresse: str = "1 Place de la Mairie 35000 Rennes",
):
    """Crée un mock de DonneesEtablissement."""
    mock = MagicMock()
    mock.unite_legale.forme_juridique.code = categorie_juridique
    mock.adresse.code_commune = code_commune
    mock.unite_legale.personne_morale_attributs.raison_sociale = raison_sociale
    mock.unite_legale.personne_physique_attributs.denomination = None
    mock.adresse_postale_legere = adresse
    return mock


def _make_mock_etablissement_no_dependents(**kwargs):
    """Crée un mock sans données dépendantes (code_commune=None, categorie_juridique=None).
    Utile pour les tests qui n'ont pas besoin de refs FK en base.
    """
    return _make_mock_etablissement(code_commune=None, categorie_juridique=None, **kwargs)


def _make_mock_api_client(etablissement_side_effect=None, with_dependents: bool = False):
    """Crée un mock du client ApiEntreprise.

    Args:
        etablissement_side_effect: Side effect pour donnees_etablissement.
        with_dependents: Si True, le mock retourne des données dépendantes valides.
    """
    mock_client = MagicMock()
    if etablissement_side_effect:
        mock_client.donnees_etablissement.side_effect = etablissement_side_effect
    else:
        if with_dependents:
            mock_client.donnees_etablissement.return_value = _make_mock_etablissement()
        else:
            mock_client.donnees_etablissement.return_value = _make_mock_etablissement_no_dependents()
    return mock_client


def _api_error_response():
    error_response = ApiErrorResponse(
        errors=[ApiErrorModel(code="ERR001", detail="Détail de l'erreur", title="Titre de l'erreur")]
    )
    return error_response


def _api_error():
    api_error = ApiError(_api_error_response())
    return api_error
