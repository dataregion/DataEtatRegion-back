"""Fixtures pour les tests des flows d'import des communes (PVD / ACV)."""

import shutil

import pytest
from batches.database import get_session_main
from sqlalchemy import delete

from models.entities.refs.Commune import Commune
from tests import TESTS_PATH

_data = TESTS_PATH / "data" / "communes"


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


@pytest.fixture
def clean_communes(session):
    yield
    session.rollback()
    session.execute(delete(Commune))
    session.commit()


@pytest.fixture
def mock_download(tmp_path, monkeypatch):
    """
    Remplace le téléchargement par une copie du fichier de test
    et redirige l'archivage vers un répertoire temporaire.
    """
    import batches.prefect.import_file_communes as import_mod

    monkeypatch.setattr(import_mod, "ARCHIVE_ROOT", tmp_path / "archives")

    def _mock(filename: str):
        def _download(url: str) -> str:
            downloaded = tmp_path / filename
            shutil.copy(_data / filename, downloaded)
            return str(downloaded)

        monkeypatch.setattr(import_mod, "download_file_from_website", _download)

    return _mock
