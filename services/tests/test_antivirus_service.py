"""Tests unitaires du service antivirus (AntivirusService)."""

from io import BytesIO
from unittest.mock import MagicMock, patch

import pytest

import clamd
from services.antivirus.antivirus_service import AntivirusService
from services.antivirus.exceptions import AntivirusScanError, VirusFoundError


@pytest.fixture
def av_service() -> AntivirusService:
    return AntivirusService(host="localhost", port=3310, timeout=5)


@pytest.fixture
def clean_csv_file(tmp_path):
    """Crée un fichier CSV temporaire propre."""
    f = tmp_path / "clean.csv"
    f.write_text("col1,col2\nval1,val2\n")
    return str(f)


class TestAntivirusServiceClean:
    """Fichier propre : le scan doit passer sans erreur."""

    def test_scan_file_clean(self, av_service, clean_csv_file):
        with patch("clamd.ClamdNetworkSocket") as mock_clamd_cls:
            mock_cd = MagicMock()
            mock_cd.instream.return_value = {"stream": ("OK", None)}
            mock_clamd_cls.return_value = mock_cd

            # Ne doit pas lever d'exception
            av_service.scan_file(clean_csv_file, context={"session_token": "tok-1", "user": "admin@test.fr"})

            mock_cd.instream.assert_called_once()


class TestAntivirusServiceSizeLimit:
    """La taille du fichier ne doit pas dépasser la limite configurée."""

    def test_scan_file_too_large_raises_scan_error(self, tmp_path):
        oversized_file = tmp_path / "oversized.csv"
        oversized_file.write_bytes(b"x" * 11)

        av_service = AntivirusService(host="localhost", port=3310, timeout=5, max_file_size_bytes=10)

        with patch("clamd.ClamdNetworkSocket") as mock_clamd_cls:
            with pytest.raises(AntivirusScanError) as exc_info:
                av_service.scan_file(str(oversized_file), context={"session_token": "tok-size"})

            assert "dépasse la limite" in exc_info.value.message
            mock_clamd_cls.assert_not_called()


class TestAntivirusServiceInfected:
    """Fichier infecté : doit lever VirusFoundError avec le nom du virus."""

    def test_scan_file_infected_raises_virus_found_error(self, av_service, clean_csv_file):
        with patch("clamd.ClamdNetworkSocket") as mock_clamd_cls:
            mock_cd = MagicMock()
            mock_cd.instream.return_value = {"stream": ("FOUND", "Eicar-Signature")}
            mock_clamd_cls.return_value = mock_cd

            with pytest.raises(VirusFoundError) as exc_info:
                av_service.scan_file(clean_csv_file, context={"session_token": "tok-2", "user": "admin@test.fr"})

            assert exc_info.value.virus_name == "Eicar-Signature"

    def test_register_file_not_called_when_infected(self, av_service, clean_csv_file):
        """Garantit que le scan bloque bien avant tout traitement aval."""
        with patch("clamd.ClamdNetworkSocket") as mock_clamd_cls:
            mock_cd = MagicMock()
            mock_cd.instream.return_value = {"stream": ("FOUND", "Win.Virus.Test")}
            mock_clamd_cls.return_value = mock_cd

            with pytest.raises(VirusFoundError):
                av_service.scan_file(clean_csv_file)


class TestAntivirusServiceUnavailable:
    """Service antivirus indisponible : doit lever AntivirusScanError (fail closed)."""

    def test_scan_file_connection_error_raises_scan_error(self, av_service, clean_csv_file):
        with patch("clamd.ClamdNetworkSocket") as mock_clamd_cls:
            mock_cd = MagicMock()
            mock_cd.instream.side_effect = clamd.ConnectionError("refused")
            mock_clamd_cls.return_value = mock_cd

            with pytest.raises(AntivirusScanError) as exc_info:
                av_service.scan_file(clean_csv_file, context={"session_token": "tok-3"})

            assert "indisponible" in exc_info.value.message

    def test_scan_file_timeout_raises_scan_error(self, av_service, clean_csv_file):
        with patch("clamd.ClamdNetworkSocket") as mock_clamd_cls:
            mock_cd = MagicMock()
            mock_cd.instream.side_effect = TimeoutError("timeout")
            mock_clamd_cls.return_value = mock_cd

            with pytest.raises(AntivirusScanError) as exc_info:
                av_service.scan_file(clean_csv_file, context={"session_token": "tok-4"})

            assert "expiré" in exc_info.value.message

    def test_scan_file_unexpected_error_raises_scan_error(self, av_service, clean_csv_file):
        with patch("clamd.ClamdNetworkSocket") as mock_clamd_cls:
            mock_cd = MagicMock()
            mock_cd.instream.side_effect = RuntimeError("boom")
            mock_clamd_cls.return_value = mock_cd

            with pytest.raises(AntivirusScanError):
                av_service.scan_file(clean_csv_file)

    def test_scan_file_nonconforming_result_raises_scan_error(self, av_service, clean_csv_file):
        """Statut renvoyé par clamd différent de OK/FOUND → AntivirusScanError."""
        with patch("clamd.ClamdNetworkSocket") as mock_clamd_cls:
            mock_cd = MagicMock()
            mock_cd.instream.return_value = {"stream": ("ERROR", None)}
            mock_clamd_cls.return_value = mock_cd

            with pytest.raises(AntivirusScanError) as exc_info:
                av_service.scan_file(clean_csv_file)

            assert "non conforme" in exc_info.value.message


class TestAntivirusServiceScannedBinaryIO:
    """Tests de la méthode scanned_binary_io."""

    @pytest.mark.parametrize(
        "input_content",
        [
            b"col1,col2\nval1,val2\n",
            b"x" * (8 * 1024 * 1024),
        ],
        ids=["small_input", "large_input_8mb"],
    )
    def test_scanned_binary_io_returns_same_content_as_input(self, av_service, input_content):
        """Le flux retourné doit contenir exactement les mêmes octets que le flux d'entrée."""
        initial_binary_io = BytesIO(input_content)

        with patch.object(av_service, "scan_file", return_value=None) as mock_scan_file:
            with av_service.scanned_binary_io(
                initial_binary_io, context={"session_token": "tok-binary-1"}
            ) as returned_binary_io:
                initial_binary_io.seek(0)
                returned_binary_io.seek(0)

                assert returned_binary_io.read() == initial_binary_io.read()
                mock_scan_file.assert_called_once()
