"""Tests unitaires du TUS (Tus Upload Server) pour l'import Chorus avec priorité sur les droits."""

import pytest
import tempfile
import os

from apis.apps.budget.routers.import_chorus import pre_create_hook
from apis.apps.budget.services.import_chorus import validate_csv_file_content
from models.connected_user import ConnectedUser
from models.exceptions import BadRequestError


class TestPreCreateHookValidation:
    """Tests de validation du pre_create_hook."""

    @pytest.mark.asyncio
    async def test_validate_metadata_missing_filename(self):
        """Le pre_create_hook doit lever une erreur si filename manque."""
        # Arrange
        user = ConnectedUser(
            {
                "sub": "test-user-123",
                "email": "test@example.com",
                "preferred_username": "testuser",
                "realm_access": {"roles": ["user"]},
            }
        )

        handler = pre_create_hook(user=user)
        metadata = {"session_token": "test-token", "uploadType": "financial-ae", "filetype": "text/csv"}

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await handler(metadata=metadata, upload_info={"size": 1000})

        assert exc_info.value.code.value == 400
        assert "Filename is required" in str(exc_info.value.api_message)

    @pytest.mark.asyncio
    async def test_validate_metadata_missing_session_token(self):
        """Le pre_create_hook doit lever une erreur si session_token manque."""
        # Arrange
        user = ConnectedUser(
            {
                "sub": "test-user-123",
                "email": "test@example.com",
                "preferred_username": "testuser",
                "realm_access": {"roles": ["user"]},
            }
        )

        handler = pre_create_hook(user=user)
        metadata = {"filename": "test.csv", "uploadType": "financial-ae", "filetype": "text/csv"}

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await handler(metadata=metadata, upload_info={"size": 1000})

        assert exc_info.value.code.value == 400
        assert "Session token is required" in str(exc_info.value.api_message)

    @pytest.mark.asyncio
    async def test_validate_metadata_missing_upload_type(self):
        """Le pre_create_hook doit lever une erreur si uploadType manque."""
        # Arrange
        user = ConnectedUser(
            {
                "sub": "test-user-123",
                "email": "test@example.com",
                "preferred_username": "testuser",
                "realm_access": {"roles": ["user"]},
            }
        )

        handler = pre_create_hook(user=user)
        metadata = {"filename": "test.csv", "session_token": "test-token", "filetype": "text/csv"}

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await handler(metadata=metadata, upload_info={"size": 1000})

        assert exc_info.value.code.value == 400
        assert "Upload type is required" in str(exc_info.value.api_message)

    @pytest.mark.asyncio
    async def test_validate_metadata_invalid_upload_type(self):
        """Le pre_create_hook doit lever une erreur si uploadType invalide."""
        # Arrange
        user = ConnectedUser(
            {
                "sub": "test-user-123",
                "email": "test@example.com",
                "preferred_username": "testuser",
                "realm_access": {"roles": ["user"]},
            }
        )

        handler = pre_create_hook(user=user)
        metadata = {
            "filename": "test.csv",
            "session_token": "test-token",
            "uploadType": "INVALID_TYPE",
            "filetype": "text/csv",
        }

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await handler(metadata=metadata, upload_info={"size": 1000})

        assert exc_info.value.code.value == 400
        assert "not allowed" in str(exc_info.value.api_message)

    @pytest.mark.asyncio
    async def test_validate_metadata_file_too_large(self):
        """Le pre_create_hook doit lever une erreur si fichier trop volumineux."""
        # Arrange
        user = ConnectedUser(
            {
                "sub": "test-user-123",
                "email": "test@example.com",
                "preferred_username": "testuser",
                "realm_access": {"roles": ["user"]},
            }
        )

        handler = pre_create_hook(user=user)
        metadata = {
            "filename": "test.csv",
            "session_token": "test-token",
            "uploadType": "financial-ae",
            "filetype": "text/csv",
            "total_ae_files": "1",
            "total_cp_files": "1",
        }

        # Fichier de taille excessive
        upload_info = {"size": 2 * 1024 * 1024 * 1024}  # 2GB

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await handler(metadata=metadata, upload_info=upload_info)

        assert exc_info.value.code.value == 413
        assert "too large" in str(exc_info.value.api_message)

    @pytest.mark.asyncio
    async def test_validate_metadata_valid_input(self):
        """Le pre_create_hook doit passer avec des métadatas valides."""
        # Arrange
        user = ConnectedUser(
            {
                "sub": "test-user-123",
                "email": "test@example.com",
                "preferred_username": "testuser",
                "realm_access": {"roles": ["user"]},
            }
        )

        handler = pre_create_hook(user=user)
        metadata = {
            "filename": "test.csv",
            "session_token": "test-token",
            "uploadType": "financial-ae",
            "filetype": "text/csv",
            "total_ae_files": "1",
            "total_cp_files": "1",
        }

        upload_info = {"size": 1000}  # Fichier petit

        # Act & Assert - ne doit pas lever d'exception
        result = await handler(metadata=metadata, upload_info=upload_info)
        assert result is None


class TestValidateCsvFileContent:
    """Tests de validation du contenu réel des fichiers CSV."""

    def test_validate_csv_file_content_valid_csv(self):
        """validate_csv_file_content doit accepter un vrai fichier CSV."""
        # Arrange - créer un fichier CSV temporaire valide
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1,col2,col3\n")
            f.write("val1,val2,val3\n")
            f.write("val4,val5,val6\n")
            temp_path = f.name

        try:
            # Act & Assert - ne doit pas lever d'exception
            validate_csv_file_content(temp_path)
        finally:
            # Cleanup
            os.unlink(temp_path)

    def test_validate_csv_file_content_pdf_file(self):
        """validate_csv_file_content doit rejeter un fichier PDF."""
        # Arrange - créer un fichier avec signature PDF
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".pdf", delete=False) as f:
            f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
            f.write(b"Some PDF content here")
            temp_path = f.name

        try:
            # Act & Assert
            with pytest.raises(BadRequestError) as exc_info:
                validate_csv_file_content(temp_path)

            assert "Le fichier n'est pas un CSV" in str(exc_info.value.api_message)
        finally:
            # Cleanup
            os.unlink(temp_path)

    def test_validate_csv_file_content_empty_file(self):
        """validate_csv_file_content doit rejeter un fichier vide."""
        # Arrange - créer un fichier vide
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            temp_path = f.name

        try:
            # Act & Assert
            with pytest.raises(BadRequestError) as exc_info:
                validate_csv_file_content(temp_path)

            assert "vide" in str(exc_info.value.api_message)
        finally:
            # Cleanup
            os.unlink(temp_path)

    def test_validate_csv_file_content_png_image(self):
        """validate_csv_file_content doit rejeter un fichier PNG."""
        # Arrange - créer un fichier avec signature PNG
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".png", delete=False) as f:
            f.write(b"\x89PNG\r\n\x1a\n")
            f.write(b"Some PNG content")
            temp_path = f.name

        try:
            # Act & Assert
            with pytest.raises(BadRequestError) as exc_info:
                validate_csv_file_content(temp_path)

            assert "Le fichier n'est pas un CSV" == str(exc_info.value.api_message)
        finally:
            # Cleanup
            os.unlink(temp_path)

    def test_validate_csv_file_content_zip_archive(self):
        """validate_csv_file_content doit rejeter un fichier ZIP."""
        # Arrange - créer un fichier avec signature ZIP
        with tempfile.NamedTemporaryFile(mode="wb", suffix=".zip", delete=False) as f:
            f.write(b"PK\x03\x04")
            f.write(b"Some ZIP content")
            temp_path = f.name

        try:
            # Act & Assert
            with pytest.raises(BadRequestError) as exc_info:
                validate_csv_file_content(temp_path)

            assert "Le fichier ne peut pas être lu comme un CSV valide" in str(exc_info.value.api_message)
        finally:
            # Cleanup
            os.unlink(temp_path)

    def test_validate_csv_file_content_invalid_csv_format(self):
        """validate_csv_file_content doit rejeter un fichier texte non-CSV."""
        # Arrange - créer un fichier texte qui n'est pas un CSV valide
        with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as f:
            f.write("This is just plain text\n")
            f.write("Not a CSV at all\n")
            f.write("No delimiters here\n")
            temp_path = f.name

        try:
            # Act & Assert - doit rejeter car pas de délimiteur CSV détectable
            with pytest.raises(BadRequestError) as exc_info:
                validate_csv_file_content(temp_path)

            assert "CSV" in str(exc_info.value.api_message)
        finally:
            # Cleanup
            os.unlink(temp_path)

    def test_validate_csv_file_content_csv_with_semicolon(self):
        """validate_csv_file_content doit accepter un CSV avec point-virgule."""
        # Arrange - créer un fichier CSV avec point-virgule
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1;col2;col3\n")
            f.write("val1;val2;val3\n")
            f.write("val4;val5;val6\n")
            temp_path = f.name

        try:
            # Act & Assert - ne doit pas lever d'exception
            validate_csv_file_content(temp_path)
        finally:
            # Cleanup
            os.unlink(temp_path)

    def test_validate_csv_file_content_csv_with_tabs(self):
        """validate_csv_file_content doit accepter un CSV avec tabulations."""
        # Arrange - créer un fichier CSV avec tabulations
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("col1\tcol2\tcol3\n")
            f.write("val1\tval2\tval3\n")
            f.write("val4\tval5\tval6\n")
            temp_path = f.name

        try:
            # Act & Assert - ne doit pas lever d'exception
            validate_csv_file_content(temp_path)
        finally:
            # Cleanup
            os.unlink(temp_path)
