"""Tests d'intégration : scan antivirus dans le flux upload_complete de l'import Chorus."""

from unittest.mock import MagicMock, patch

import pytest

from models.exceptions import BadRequestError

from apis.config.current import override_config
from apis.apps.budget.services.import_chorus import upload_complete


@pytest.fixture(scope="session")
def antivirus_config(config):
    av_conf = config.antivirus
    overriden = av_conf.model_copy(update={"enabled": True})
    override_config("antivirus", overriden)


@pytest.fixture(scope="session")
def antivirus_config__disabled(config):
    av_conf = config.antivirus
    overriden = av_conf.model_copy(update={"enabled": False})
    override_config("antivirus", overriden)


def _mock_upload_session(register_file_return_value=None):

    if register_file_return_value is None:
        register_file_return_value = MagicMock(is_complete=False, total_received=1, total_expected=2)

    mock_session = MagicMock()
    mock_session.register_file.return_value = register_file_return_value
    mock_session.finalize.return_value = (
        "/tmp/fake_ae_file_path",
        "/tmp/fake_cp_file_path",
    )

    return mock_session


def _mock_session_service(mock_session):
    mock_session_svc = MagicMock()
    mock_session_svc.borrow_session.return_value.__enter__ = MagicMock(return_value=mock_session)
    mock_session_svc.borrow_session.return_value.__exit__ = MagicMock(return_value=False)
    return mock_session_svc


class TestUploadCompleteAntivirusIntegration:
    """
    Vérifie que upload_complete appelle le scan antivirus et bloque
    register_file si le scan échoue.
    """

    def _base_metadata(self, tmp_path):
        f = tmp_path / "ae_test.csv"
        f.write_text("col1,col2\nval1,val2\n")
        return str(f), {
            "filename": "ae_test.csv",
            "session_token": "session-av-test",
            "uploadType": "financial-ae",
            "indice": "0",
            "filetype": "text/csv",
        }

    def test_infected_file_blocks_register(self, antivirus_config, tmp_path, mock_connected_user):
        """Un fichier infecté ne doit pas appeler register_file."""
        file_path, metadata = self._base_metadata(tmp_path)
        user = mock_connected_user
        db = MagicMock()

        with (
            patch("services.antivirus.antivirus_service.clamd.ClamdNetworkSocket") as mock_clamd_cls,
            patch("apis.apps.budget.services.import_chorus.UploadSessionService") as mock_session_svc,
        ):
            mock_cd = MagicMock()
            mock_cd.instream.return_value = {"stream": ("FOUND", "Eicar-Signature")}
            mock_clamd_cls.return_value = mock_cd

            from apis.apps.budget.services.import_chorus import upload_complete

            with pytest.raises(BadRequestError) as exc_info:
                upload_complete(db=db, user=user, file_path=file_path, metadata=metadata)

            assert "virus found" in str(exc_info.value.api_message).lower()
            # register_file ne doit jamais être appelé
            mock_session_svc.return_value.register_file.assert_not_called()

    def test_clean_file_proceeds_to_register(self, antivirus_config, tmp_path, mock_connected_user):
        """Un fichier propre doit poursuivre vers register_file."""
        file_path, metadata = self._base_metadata(tmp_path)
        user = mock_connected_user
        db = MagicMock()

        with (
            patch("services.antivirus.antivirus_service.clamd.ClamdNetworkSocket") as mock_clamd_cls,
            patch("apis.apps.budget.services.import_chorus._get_upload_session_service") as mock_get_svc,
        ):
            mock_cd = MagicMock()
            mock_cd.instream.return_value = {"stream": ("OK", None)}
            mock_clamd_cls.return_value = mock_cd

            ##
            mock_session = _mock_upload_session()
            mock_session_svc = _mock_session_service(mock_session)
            mock_get_svc.return_value = mock_session_svc

            upload_complete(db=db, user=user, file_path=file_path, metadata=metadata)

            mock_session.register_file.assert_called_once()

    def test_antivirus_disabled_skips_scan(self, antivirus_config__disabled, tmp_path, mock_connected_user):
        """Quand antivirus.enabled=False, le scan ne doit pas être appelé."""
        file_path, metadata = self._base_metadata(tmp_path)
        user = mock_connected_user
        db = MagicMock()

        with (
            patch("apis.apps.budget.services.import_chorus._get_upload_session_service") as mock_get_svc,
        ):
            mock_session = _mock_upload_session()
            mock_session_svc = _mock_session_service(mock_session)
            mock_get_svc.return_value = mock_session_svc

            # Ne lève pas d'exception et n'appelle pas clamd
            upload_complete(db=db, user=user, file_path=file_path, metadata=metadata)
            mock_session.register_file.assert_called_once()
