"""Tests unitaires pour le service de gestion des sessions d'upload."""

import tempfile
import pytest
from pathlib import Path

from services.audits.upload_session import SessionState, UploadSessionService


class TestSessionState:
    """Tests de la classe SessionState."""

    def test_session_state_is_complete_when_all_files_received(self):
        """Test que is_complete retourne True quand tous les fichiers sont reçus."""
        state = SessionState(
            session_token="test-token",
            total_ae_files=2,
            total_cp_files=3,
            year=2024,
            source_region="BRETAGNE",
            username="test@example.com",
        )
        state.received_ae_files = ["file1.csv", "file2.csv"]
        state.received_cp_files = ["file3.csv", "file4.csv", "file5.csv"]

        assert state.is_complete is True

    def test_session_state_is_not_complete_when_files_missing(self):
        """Test que is_complete retourne False quand des fichiers manquent."""
        state = SessionState(
            session_token="test-token",
            total_ae_files=2,
            total_cp_files=3,
            year=2024,
            source_region="BRETAGNE",
            username="test@example.com",
        )
        state.received_ae_files = ["file1.csv"]
        state.received_cp_files = ["file3.csv", "file4.csv"]

        assert state.is_complete is False

    def test_session_state_total_received(self):
        """Test le calcul du total de fichiers reçus."""
        state = SessionState(
            session_token="test-token",
            total_ae_files=2,
            total_cp_files=3,
            year=2024,
            source_region="BRETAGNE",
            username="test@example.com",
        )
        state.received_ae_files = ["file1.csv", "file2.csv"]
        state.received_cp_files = ["file3.csv"]

        assert state.total_received == 3

    def test_session_state_total_expected(self):
        """Test le calcul du total de fichiers attendus."""
        state = SessionState(
            session_token="test-token",
            total_ae_files=5,
            total_cp_files=7,
            year=2024,
            source_region="BRETAGNE",
            username="test@example.com",
        )

        assert state.total_expected == 12

    def test_session_state_serialization(self):
        """Test la sérialisation/désérialisation du SessionState."""
        state = SessionState(
            session_token="test-token",
            total_ae_files=2,
            total_cp_files=3,
            year=2024,
            source_region="BRETAGNE",
            username="test@example.com",
            client_id="test-client",
        )
        state.file_hashes = {"file1.csv": "abc123", "file2.csv": "def456"}
        state.final_ae_file = "/path/to/final_ae.csv"
        state.final_cp_file = "/path/to/final_cp.csv"

        # Sérialiser
        data = state.to_dict()
        assert isinstance(data, dict)
        assert data["session_token"] == "test-token"
        assert data["file_hashes"] == {"file1.csv": "abc123", "file2.csv": "def456"}
        assert data["final_ae_file"] == "/path/to/final_ae.csv"
        assert data["final_cp_file"] == "/path/to/final_cp.csv"

        # Désérialiser
        restored = SessionState.from_dict(data)
        assert restored.session_token == state.session_token
        assert restored.file_hashes == state.file_hashes
        assert restored.final_ae_file == state.final_ae_file
        assert restored.final_cp_file == state.final_cp_file


class TestUploadSessionService:
    """Tests du service de gestion des sessions d'upload."""

    @pytest.fixture
    def temp_dirs(self):
        """Crée des répertoires temporaires pour les tests."""
        with tempfile.TemporaryDirectory() as sessions_dir:
            with tempfile.TemporaryDirectory() as final_dir:
                yield sessions_dir, final_dir

    @pytest.fixture
    def service(self, temp_dirs):
        """Crée une instance du service avec des répertoires temporaires."""
        sessions_dir, final_dir = temp_dirs
        return UploadSessionService(sessions_folder=sessions_dir, final_folder=final_dir)

    def test_calculate_file_hash(self, service, tmp_path):
        """Test le calcul de hash SHA256 d'un fichier."""
        # Créer un fichier temporaire avec du contenu connu
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2,col3\nval1,val2,val3\n", encoding="utf-8")

        # Calculer le hash
        file_hash = service._calculate_file_hash(str(test_file))

        # Vérifier que c'est un hash SHA256 valide (64 caractères hexadécimaux)
        assert len(file_hash) == 64
        assert all(c in "0123456789abcdef" for c in file_hash)

        # Vérifier que le même fichier produit le même hash
        file_hash2 = service._calculate_file_hash(str(test_file))
        assert file_hash == file_hash2

    def test_register_file_stores_hash(self, service, tmp_path):
        """Test que register_file stocke le hash du fichier."""
        # Créer un fichier temporaire
        test_file = tmp_path / "test_ae.csv"
        test_file.write_text("col1,col2\nval1,val2\n", encoding="utf-8")

        # Enregistrer le fichier
        state = service.register_file(
            file_path=str(test_file),
            session_token="test-session",
            upload_type="financial-ae",
            total_ae_files=1,
            total_cp_files=1,
            year=2024,
            source_region="BRETAGNE",
            username="test@example.com",
        )

        # Vérifier que le hash a été stocké
        assert len(state.file_hashes) == 1
        # Récupérer le hash du fichier déplacé
        moved_file_path = state.received_ae_files[0]
        assert moved_file_path in state.file_hashes
        assert len(state.file_hashes[moved_file_path]) == 64

    def test_finalize_session_stores_final_files(self, service, tmp_path):
        """Test que finalize_session stocke les chemins des fichiers finaux."""
        # Créer deux fichiers AE et deux fichiers CP
        ae_file1 = tmp_path / "ae1.csv"
        ae_file1.write_text("col1,col2\nae1_val1,ae1_val2\n", encoding="utf-8")
        ae_file2 = tmp_path / "ae2.csv"
        ae_file2.write_text("col1,col2\nae2_val1,ae2_val2\n", encoding="utf-8")

        cp_file1 = tmp_path / "cp1.csv"
        cp_file1.write_text("col1,col2\ncp1_val1,cp1_val2\n", encoding="utf-8")
        cp_file2 = tmp_path / "cp2.csv"
        cp_file2.write_text("col1,col2\ncp2_val1,cp2_val2\n", encoding="utf-8")

        # Enregistrer les fichiers
        session_token = "complete-session"
        service.register_file(
            file_path=str(ae_file1),
            session_token=session_token,
            upload_type="financial-ae",
            total_ae_files=2,
            total_cp_files=2,
            year=2024,
            source_region="BRETAGNE",
            username="test@example.com",
        )
        service.register_file(
            file_path=str(ae_file2),
            session_token=session_token,
            upload_type="financial-ae",
            total_ae_files=2,
            total_cp_files=2,
            year=2024,
            source_region="BRETAGNE",
            username="test@example.com",
        )
        service.register_file(
            file_path=str(cp_file1),
            session_token=session_token,
            upload_type="financial-cp",
            total_ae_files=2,
            total_cp_files=2,
            year=2024,
            source_region="BRETAGNE",
            username="test@example.com",
        )
        service.register_file(
            file_path=str(cp_file2),
            session_token=session_token,
            upload_type="financial-cp",
            total_ae_files=2,
            total_cp_files=2,
            year=2024,
            source_region="BRETAGNE",
            username="test@example.com",
        )

        # Finaliser la session
        ae_final, cp_final = service.finalize_session(session_token)

        # Vérifier que l'état contient les fichiers finaux
        state = service.get_session_state(session_token)
        assert state is not None
        assert state.final_ae_file == ae_final
        assert state.final_cp_file == cp_final
        assert Path(ae_final).exists()
        assert Path(cp_final).exists()
