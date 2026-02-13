"""Tests unitaires du TUS (Tus Upload Server) pour l'import Chorus avec priorité sur les droits."""

import pytest

from apis.apps.budget.routers.import_chorus import pre_create_hook
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
    async def test_validate_metadata_missing_filetype(self):
        """Le pre_create_hook doit lever une erreur si filetype manque."""
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
        metadata = {"filename": "test.csv", "session_token": "test-token", "uploadType": "financial-ae"}

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await handler(metadata=metadata, upload_info={"size": 1000})

        assert exc_info.value.code.value == 400
        assert "File type is required" in str(exc_info.value.api_message)

    @pytest.mark.asyncio
    async def test_validate_metadata_invalid_filetype(self):
        """Le pre_create_hook doit lever une erreur si filetype invalide."""
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
            "filename": "test.xlsx",
            "session_token": "test-token",
            "uploadType": "financial-ae",
            "filetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        }

        # Act & Assert
        with pytest.raises(BadRequestError) as exc_info:
            await handler(metadata=metadata, upload_info={"size": 1000})

        assert exc_info.value.code.value == 400
        assert "not allowed" in str(exc_info.value.api_message)

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
