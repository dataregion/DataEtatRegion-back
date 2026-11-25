import json
from unittest.mock import patch

import pytest

from app.tasks.files.file_task import _parse_generic
from models.value_objects.common import DataType


@pytest.fixture
def upload_folder(app, tmp_path):
    upload = tmp_path / "upload"
    upload.mkdir()
    with app.app_context(), patch.dict(app.config, {"UPLOAD_FOLDER": str(upload), "SPLIT_FILE_LINE": 2}):
        yield upload


@pytest.fixture
def fichier(tmp_path):
    f = tmp_path / "AE_TEST.csv"
    f.write_text("a,b\n1,2\n3,4\n5,6\n")
    return f


def _parse(fichier):
    return _parse_generic(DataType.FINANCIAL_DATA_AE, str(fichier), "53", 2026, json.dumps({"sep": ","}), {}, {})


def test_split_dans_dossier_temporaire_supprime(upload_folder, fichier):
    chunks_lus = []

    def _fake_parse_ae(output_file, ae_list, *args):
        chunks_lus.append(output_file)
        return ae_list

    with patch("app.tasks.files.file_task._parse_ae", side_effect=_fake_parse_ae):
        _parse(fichier)

    assert len(chunks_lus) == 2
    assert all(f.startswith(str(upload_folder / "split_")) for f in chunks_lus)
    assert list(upload_folder.iterdir()) == []


def test_split_dossier_temporaire_supprime_en_cas_d_erreur(upload_folder, fichier):
    with patch("app.tasks.files.file_task._parse_ae", side_effect=ValueError("boom")):
        with pytest.raises(ValueError):
            _parse(fichier)

    assert list(upload_folder.iterdir()) == []
