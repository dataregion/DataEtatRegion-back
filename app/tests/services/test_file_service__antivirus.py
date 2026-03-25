"""
Tests unitaires – scan antivirus dans check_file_and_save
"""

from unittest.mock import MagicMock, patch

import pytest
from flask import Flask

from app.exceptions.exceptions import InvalidFile
from app.services.file_service import check_file_and_save
from services.antivirus.exceptions import AntivirusScanError, VirusFoundError

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

AV_CONFIG_ENABLED = {
    "ENABLED": True,
    "HOST": "localhost",
    "PORT": 3310,
    "TIMEOUT": 60,
    "MAX_FILE_SIZE_BYTES": 26214400,
}

AV_CONFIG_DISABLED = {
    "ENABLED": False,
    "HOST": "localhost",
    "PORT": 3310,
    "TIMEOUT": 60,
    "MAX_FILE_SIZE_BYTES": 26214400,
}


def _make_app(av_config: dict | None) -> Flask:
    """Crée une application Flask minimaliste pour les tests du service de fichier."""
    app = Flask(__name__)
    app.config["UPLOAD_FOLDER"] = "/tmp"
    app.config["TESTING"] = True
    if av_config is not None:
        app.config["ANTIVIRUS"] = av_config
    return app


def _make_file_storage(filename: str = "test.csv") -> MagicMock:
    """Fabrique un faux FileStorage werkzeug."""
    mock_file = MagicMock()
    mock_file.filename = filename
    mock_file.save = MagicMock()
    return mock_file


# ---------------------------------------------------------------------------
# Tests – antivirus activé
# ---------------------------------------------------------------------------


def test_virus_found_raises_invalid_file_and_deletes_file():
    """Un fichier infecté doit être supprimé et lever InvalidFile(VirusFound)."""
    app = _make_app(AV_CONFIG_ENABLED)
    mock_file = _make_file_storage("rapport.csv")

    with app.app_context():
        with (
            patch("app.services.file_service.AntivirusService") as MockAV,
            patch("app.services.file_service.os.remove") as mock_remove,
        ):
            MockAV.return_value.scan_file.side_effect = VirusFoundError(virus_name="EICAR-Test-File")

            with pytest.raises(InvalidFile) as exc_info:
                check_file_and_save(mock_file)

    assert exc_info.value.name == "VirusFound"
    mock_remove.assert_called_once()


def test_antivirus_unavailable_raises_invalid_file_and_deletes_file():
    """Une indisponibilité antivirus doit être refusée avec fail-closed (InvalidFile)."""
    app = _make_app(AV_CONFIG_ENABLED)
    mock_file = _make_file_storage("rapport.csv")

    with app.app_context():
        with (
            patch("app.services.file_service.AntivirusService") as MockAV,
            patch("app.services.file_service.os.remove") as mock_remove,
        ):
            MockAV.return_value.scan_file.side_effect = AntivirusScanError(message="Service antivirus indisponible")

            with pytest.raises(InvalidFile) as exc_info:
                check_file_and_save(mock_file)

    assert exc_info.value.name == "AntivirusScanFailed"
    mock_remove.assert_called_once()


def test_clean_file_returns_path():
    """Un fichier sain doit retourner le chemin sans lever d'exception."""
    app = _make_app(AV_CONFIG_ENABLED)
    mock_file = _make_file_storage("rapport.csv")

    with app.app_context():
        with (
            patch("app.services.file_service.AntivirusService") as MockAV,
            patch("app.services.file_service.os.remove") as mock_remove,
        ):
            MockAV.return_value.scan_file.return_value = None  # scan OK

            result = check_file_and_save(mock_file)

    assert result.endswith("rapport.csv")
    mock_remove.assert_not_called()


# ---------------------------------------------------------------------------
# Tests – antivirus désactivé
# ---------------------------------------------------------------------------


def test_av_disabled_skips_scan_and_returns_path():
    """Si l'antivirus est désactivé, la sauvegarde réussit sans appel au scanner."""
    app = _make_app(AV_CONFIG_DISABLED)
    mock_file = _make_file_storage("rapport.csv")

    with app.app_context():
        with (
            patch("app.services.file_service.AntivirusService") as MockAV,
        ):
            result = check_file_and_save(mock_file)

    MockAV.assert_not_called()
    assert result.endswith("rapport.csv")


def test_av_not_configured_skips_scan():
    """Si la config antivirus est absente, la sauvegarde réussit sans appel au scanner."""
    app = _make_app(av_config=None)
    mock_file = _make_file_storage("rapport.csv")

    with app.app_context():
        with (
            patch("app.services.file_service.AntivirusService") as MockAV,
        ):
            result = check_file_and_save(mock_file)

    MockAV.assert_not_called()
    assert result.endswith("rapport.csv")


# ---------------------------------------------------------------------------
# Tests – contexte journalisation
# ---------------------------------------------------------------------------


def test_scan_context_includes_filename():
    """Le nom du fichier est transmis dans le contexte de scan."""
    app = _make_app(AV_CONFIG_ENABLED)
    mock_file = _make_file_storage("rapport.csv")

    with app.app_context():
        with patch("app.services.file_service.AntivirusService") as MockAV:
            MockAV.return_value.scan_file.return_value = None

            check_file_and_save(mock_file)

    call_kwargs = MockAV.return_value.scan_file.call_args
    context = call_kwargs.kwargs["context"]
    assert context["filename"] == "rapport.csv"


# ---------------------------------------------------------------------------
# Tests – suppression silencieuse même si os.remove échoue
# ---------------------------------------------------------------------------


def test_file_removal_failure_does_not_shadow_antivirus_error():
    """Si la suppression échoue, l'exception antivirus est quand même propagée."""
    app = _make_app(AV_CONFIG_ENABLED)
    mock_file = _make_file_storage("rapport.csv")

    with app.app_context():
        with (
            patch("app.services.file_service.AntivirusService") as MockAV,
            patch("app.services.file_service.os.remove", side_effect=OSError("Permission denied")),
        ):
            MockAV.return_value.scan_file.side_effect = VirusFoundError(virus_name="EICAR")

            with pytest.raises(InvalidFile) as exc_info:
                check_file_and_save(mock_file)

    assert exc_info.value.name == "VirusFound"
