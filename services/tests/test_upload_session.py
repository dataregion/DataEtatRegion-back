import multiprocessing
import tempfile
import time
from pathlib import Path

import pytest
from testcontainers.postgres import PostgresContainer
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from models.value_objects.UploadType import UploadType
from services.audits.upload_session import SessionState, UploadSessionService


@pytest.fixture(scope="module")
def pg_container():
    with PostgresContainer("postgres:15-alpine") as container:
        yield container


@pytest.fixture
def pg_session_factory(pg_container):
    dsn = _pg_dsn(pg_container)
    engine = create_engine(dsn)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    def factory():
        return session_factory()

    return factory


@pytest.fixture
def pg_dsn(pg_container):
    return _pg_dsn(pg_container)


def _pg_dsn(pg_container):
    """DSN libpq transmissible à un sous-processus."""
    return pg_container.get_connection_url()


def _create_csv_file(folder: Path, filename: str, rows: list[str]) -> str:
    file_path = folder / filename
    file_path.write_text("col1,col2\n" + "\n".join(rows) + "\n", encoding="utf-8")
    return str(file_path)


def _hold_session_lock(
    sessions_folder: str,
    final_folder: str,
    session_token: str,
    db_dsn: str,
    ready_queue,
) -> None:
    engine = create_engine(db_dsn)
    session_factory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    service = UploadSessionService(
        sessions_folder=sessions_folder,
        final_folder=final_folder,
        db_session_factory=session_factory,
    )
    with service.borrow_session(session_token):
        ready_queue.put("locked")
        time.sleep(0.75)


class TestUploadSessionLock:
    def test_upload_session_with_ex(self, tmp_path, pg_session_factory):
        sessions_folder = tmp_path / "sessions"
        final_folder = tmp_path / "final"
        input_folder = tmp_path / "input"
        input_folder.mkdir()

        service = UploadSessionService(
            str(sessions_folder),
            str(final_folder),
            db_session_factory=pg_session_factory,
        )

        with pytest.raises(RuntimeError, match="Simulated error during session"):
            with service.borrow_session("session-2") as _:
                raise RuntimeError("Simulated error during session")

        with service.borrow_session("session-2") as _:
            pass

    def test_upload_session_register_and_finalize(self, tmp_path, pg_session_factory):
        sessions_folder = tmp_path / "sessions"
        final_folder = tmp_path / "final"
        input_folder = tmp_path / "input"
        input_folder.mkdir()

        service = UploadSessionService(
            str(sessions_folder),
            str(final_folder),
            db_session_factory=pg_session_factory,
        )

        ae_file_1 = _create_csv_file(input_folder, "ae_1.csv", ["a,1"])
        ae_file_2 = _create_csv_file(input_folder, "ae_2.csv", ["b,2"])
        cp_file_1 = _create_csv_file(input_folder, "cp_1.csv", ["c,3"])

        with service.borrow_session("session-1") as session:
            assert session.id == "session-1"
            assert session.state is None
            first_state = session.register_file(
                file_path=ae_file_1,
                upload_type=UploadType.FINANCIAL_AE.value,
                total_ae_files=2,
                total_cp_files=1,
                year=2024,
                source_region="BRETAGNE",
                username="user@example.com",
                client_id="budget-app",
            )
            assert first_state.total_received == 1

        with service.borrow_session("session-1") as session:
            session.register_file(
                file_path=ae_file_2,
                upload_type=UploadType.FINANCIAL_AE.value,
                total_ae_files=2,
                total_cp_files=1,
                year=2024,
                source_region="BRETAGNE",
                username="user@example.com",
                client_id="budget-app",
            )
            session.register_file(
                file_path=cp_file_1,
                upload_type=UploadType.FINANCIAL_CP.value,
                total_ae_files=2,
                total_cp_files=1,
                year=2024,
                source_region="BRETAGNE",
                username="user@example.com",
                client_id="budget-app",
            )

            assert session.state is not None
            assert session.state.is_complete is True
            ae_final_path, cp_final_path = session.finalize()

        ae_content = Path(ae_final_path).read_text(encoding="utf-8")
        cp_content = Path(cp_final_path).read_text(encoding="utf-8")
        saved_state = service.get_session_state("session-1")

        assert ae_content == "col1,col2\na,1\nb,2\n"
        assert cp_content == "col1,col2\nc,3\n"
        assert saved_state is not None
        assert saved_state.final_ae_file == ae_final_path
        assert saved_state.final_cp_file == cp_final_path

    def test_borrow_session_blocks_concurrent_access(self, tmp_path, pg_session_factory, pg_dsn):
        sessions_folder = tmp_path / "sessions"
        final_folder = tmp_path / "final"
        ready_queue = multiprocessing.Queue()

        process = multiprocessing.Process(
            target=_hold_session_lock,
            args=(str(sessions_folder), str(final_folder), "session-locked", pg_dsn, ready_queue),
        )
        process.start()

        assert ready_queue.get(timeout=2) == "locked"

        service = UploadSessionService(
            str(sessions_folder),
            str(final_folder),
            db_session_factory=pg_session_factory,
        )
        start = time.monotonic()
        with service.borrow_session("session-locked"):
            waited = time.monotonic() - start

        process.join(timeout=2)

        assert process.exitcode == 0
        assert waited >= 0.6

    def test_borrow_session_raises_timeout_when_lock_is_busy(self, tmp_path, pg_session_factory, pg_dsn):
        sessions_folder = tmp_path / "sessions"
        final_folder = tmp_path / "final"
        ready_queue = multiprocessing.Queue()

        process = multiprocessing.Process(
            target=_hold_session_lock,
            args=(str(sessions_folder), str(final_folder), "session-timeout", pg_dsn, ready_queue),
        )
        process.start()

        assert ready_queue.get(timeout=2) == "locked"

        service = UploadSessionService(
            str(sessions_folder),
            str(final_folder),
            db_session_factory=pg_session_factory,
            session_lock_timeout_seconds=0.2,
            session_lock_retry_interval_seconds=0.02,
        )

        with pytest.raises(TimeoutError):
            with service.borrow_session("session-timeout"):
                pass

        process.join(timeout=2)
        assert process.exitcode == 0


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

        data = state.to_dict()
        assert isinstance(data, dict)
        assert data["session_token"] == "test-token"
        assert data["file_hashes"] == {"file1.csv": "abc123", "file2.csv": "def456"}
        assert data["final_ae_file"] == "/path/to/final_ae.csv"
        assert data["final_cp_file"] == "/path/to/final_cp.csv"

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
    def service(self, temp_dirs, pg_session_factory):
        """Crée une instance du service avec des répertoires temporaires."""
        sessions_dir, final_dir = temp_dirs
        return UploadSessionService(
            sessions_folder=sessions_dir,
            final_folder=final_dir,
            db_session_factory=pg_session_factory,
        )

    def test_calculate_file_hash(self, service, tmp_path):
        """Test le calcul de hash SHA256 d'un fichier."""
        test_file = tmp_path / "test.csv"
        test_file.write_text("col1,col2,col3\nval1,val2,val3\n", encoding="utf-8")

        file_hash = service._calculate_file_hash(str(test_file))

        assert len(file_hash) == 64
        assert all(c in "0123456789abcdef" for c in file_hash)

        file_hash2 = service._calculate_file_hash(str(test_file))
        assert file_hash == file_hash2

    def test_register_file_stores_hash(self, service: UploadSessionService, tmp_path):
        """Test que register_file stocke le hash du fichier."""
        test_file = tmp_path / "test_ae.csv"
        test_file.write_text("col1,col2\nval1,val2\n", encoding="utf-8")

        with service.borrow_session("test-session") as upload_session:
            state = upload_session.register_file(
                file_path=str(test_file),
                upload_type="financial-ae",
                total_ae_files=1,
                total_cp_files=1,
                year=2024,
                source_region="BRETAGNE",
                username="test@example.com",
            )

        assert len(state.file_hashes) == 1
        moved_file_path = state.received_ae_files[0]
        assert moved_file_path in state.file_hashes
        assert len(state.file_hashes[moved_file_path]) == 64

    def test_finalize_session_stores_final_files(self, service: UploadSessionService, tmp_path):
        """Test que finalize_session stocke les chemins des fichiers finaux."""
        ae_file1 = tmp_path / "ae1.csv"
        ae_file1.write_text("col1,col2\nae1_val1,ae1_val2\n", encoding="utf-8")
        ae_file2 = tmp_path / "ae2.csv"
        ae_file2.write_text("col1,col2\nae2_val1,ae2_val2\n", encoding="utf-8")

        cp_file1 = tmp_path / "cp1.csv"
        cp_file1.write_text("col1,col2\ncp1_val1,cp1_val2\n", encoding="utf-8")
        cp_file2 = tmp_path / "cp2.csv"
        cp_file2.write_text("col1,col2\ncp2_val1,cp2_val2\n", encoding="utf-8")

        session_token = "complete-session"
        with service.borrow_session(session_token) as upload_session:
            upload_session.register_file(
                file_path=str(ae_file1),
                upload_type="financial-ae",
                total_ae_files=2,
                total_cp_files=2,
                year=2024,
                source_region="BRETAGNE",
                username="test@example.com",
            )
            upload_session.register_file(
                file_path=str(ae_file2),
                upload_type="financial-ae",
                total_ae_files=2,
                total_cp_files=2,
                year=2024,
                source_region="BRETAGNE",
                username="test@example.com",
            )
            upload_session.register_file(
                file_path=str(cp_file1),
                upload_type="financial-cp",
                total_ae_files=2,
                total_cp_files=2,
                year=2024,
                source_region="BRETAGNE",
                username="test@example.com",
            )
            upload_session.register_file(
                file_path=str(cp_file2),
                upload_type="financial-cp",
                total_ae_files=2,
                total_cp_files=2,
                year=2024,
                source_region="BRETAGNE",
                username="test@example.com",
            )

            ae_final, cp_final = upload_session.finalize()

        state = service.get_session_state(session_token)
        assert state is not None
        assert state.final_ae_file == ae_final
        assert state.final_cp_file == cp_final
        assert Path(ae_final).exists()
        assert Path(cp_final).exists()
