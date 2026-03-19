"""
Service de gestion des sessions d'upload multi-fichiers.

Ce service permet de :
- Tracker les fichiers reçus par session_token
- Détecter quand tous les fichiers d'une session sont reçus
- Concaténer les fichiers CSV AE et CP en fichiers uniques
- Conserver l'historique des sessions pour analyse

## Stockage des sessions

Les sessions d'upload sont stockées dans des fichiers JSON au format :
`{sessions_folder}/{session_token}.json`

Chaque fichier de session contient :
- Les métadonnées de la session (token, année, région, utilisateur, etc.)
- La liste des fichiers reçus (AE et CP)
- Le hash SHA256 de chaque fichier uploadé
- Les chemins des fichiers finaux concaténés (après finalisation)

**IMPORTANT** : Les fichiers de session sont conservés indéfiniment après traitement
pour permettre l'audit et l'analyse. Seuls les fichiers temporaires sont supprimés.

## Structure du SessionState (JSON)

```json
{
  "session_token": "uuid-v4",
  "total_ae_files": 2,
  "total_cp_files": 3,
  "year": 2024,
  "source_region": "BRETAGNE",
  "username": "user@example.com",
  "client_id": "budget-app",
  "received_ae_files": ["/path/to/temp/001_financial-ae_file1.csv", ...],
  "received_cp_files": ["/path/to/temp/001_financial-cp_file1.csv", ...],
  "original_ae_filenames": ["file1.csv", "file2.csv"],
  "original_cp_filenames": ["file3.csv", "file4.csv", "file5.csv"],
  "file_hashes": {
    "/path/to/temp/001_financial-ae_file1.csv": "sha256_hash_1",
    "/path/to/temp/002_financial-ae_file2.csv": "sha256_hash_2",
    ...
  },
  "final_ae_file": "/path/to/final/file1_2_AE_2024.csv",
  "final_cp_file": "/path/to/final/file3_3_CP_2024.csv"
}
```

## Cycle de vie d'une session

1. **Création** : Premier fichier uploadé → création du SessionState
2. **Enregistrement** : Chaque fichier est hashé (SHA256) puis déplacé dans le dossier temporaire
3. **Finalisation** : Quand tous les fichiers sont reçus → concaténation des CSV
4. **Sauvegarde** : Le SessionState final est sauvegardé avec les chemins finaux
5. **Nettoyage** : Les fichiers temporaires sont supprimés, le JSON de session est **conservé**
"""

import hashlib
import json
import logging
import os
import shutil
import time
from contextlib import contextmanager
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Callable, Iterator, Optional

from models.value_objects.UploadType import UploadType

logger = logging.getLogger(__name__)


@dataclass
class SessionState:
    """État d'une session d'upload"""

    session_token: str
    total_ae_files: int
    total_cp_files: int
    year: int
    source_region: str
    username: str
    client_id: Optional[str] = None
    received_ae_files: list[str] = field(default_factory=list)
    received_cp_files: list[str] = field(default_factory=list)
    original_ae_filenames: list[str] = field(default_factory=list)
    original_cp_filenames: list[str] = field(default_factory=list)
    # Hash SHA256 de chaque fichier uploadé (clé: chemin du fichier, valeur: hash)
    file_hashes: dict[str, str] = field(default_factory=dict)
    # Chemins des fichiers finaux concaténés
    final_ae_file: Optional[str] = None
    final_cp_file: Optional[str] = None

    @property
    def is_complete(self) -> bool:
        """Vérifie si tous les fichiers de la session ont été reçus"""
        return len(self.received_ae_files) == self.total_ae_files and len(self.received_cp_files) == self.total_cp_files

    @property
    def total_received(self) -> int:
        """Nombre total de fichiers reçus"""
        return len(self.received_ae_files) + len(self.received_cp_files)

    @property
    def total_expected(self) -> int:
        """Nombre total de fichiers attendus"""
        return self.total_ae_files + self.total_cp_files

    def to_dict(self) -> dict:
        """Convertit en dictionnaire pour la sérialisation JSON"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "SessionState":
        """Crée une instance depuis un dictionnaire"""
        return cls(**data)


class PgAdvisoryLock:
    """Verrou inter-process via PostgreSQL advisory locks (session-level).

    Utilise pg_advisory_try_lock / pg_advisory_unlock plutôt que fcntl.flock,
    ce qui garantit la portabilité entre processus distribués tant qu'ils
    partagent la même instance PostgreSQL.
    """

    def __init__(
        self,
        session_factory: Callable[[], Any],
        lock_key: int,
        timeout_seconds: float = 10.0,
        retry_interval_seconds: float = 0.05,
    ):
        self.session_factory = session_factory
        self.lock_key = lock_key
        self.timeout_seconds = timeout_seconds
        self.retry_interval_seconds = retry_interval_seconds
        self._session: Optional[Any] = None
        self._active = False

    @staticmethod
    def token_to_lock_key(session_token: str) -> int:
        """Dérive une clé bigint stable depuis un token de session.

        Utilise les 8 premiers octets d'un SHA-256, interprétés en big-endian
        signé pour rester dans les bornes de int64 PostgreSQL.
        """
        digest = hashlib.sha256(session_token.encode()).digest()
        return int.from_bytes(digest[:8], "big", signed=True)

    @property
    def is_active(self) -> bool:
        """Indique si le verrou advisory est actuellement acquis."""
        return self._active

    def __enter__(self) -> "PgAdvisoryLock":
        self._session = self.session_factory()
        connection = self._session.connection()
        deadline = time.monotonic() + self.timeout_seconds
        while True:
            acquired = connection.exec_driver_sql("SELECT pg_try_advisory_lock(%s)", (self.lock_key,)).scalar()
            if acquired:
                break
            if time.monotonic() >= deadline:
                self._session.close()
                self._session = None
                raise TimeoutError(
                    f"Could not acquire advisory lock for key {self.lock_key} within {self.timeout_seconds} seconds"
                )
            time.sleep(self.retry_interval_seconds)
        self._active = True
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._session is None:
            return
        try:
            self._session.connection().exec_driver_sql("SELECT pg_advisory_unlock(%s)", (self.lock_key,))
        finally:
            self._session.close()
            self._session = None
            self._active = False


class UploadSession:
    """Session d'upload verrouillée pour effectuer des opérations atomiques."""

    def __init__(
        self,
        service: "UploadSessionService",
        session_token: str,
        lock: PgAdvisoryLock,
        state: Optional[SessionState] = None,
    ):
        self._service = service
        self._session_token = session_token
        self._lock = lock
        self._state = state

    def _ensure_lock_is_active(self) -> None:
        """Empêche l'utilisation de la session en dehors du contexte d'emprunt."""
        if not self._lock.is_active:
            raise RuntimeError(
                "UploadSession must be used inside UploadSessionService.borrow_session while the session lock is active"
            )

    @property
    def id(self) -> str:
        """Identifiant de la session."""
        return self._session_token

    @property
    def state(self) -> Optional[SessionState]:
        """État courant de la session."""
        return self._state

    def register_file(
        self,
        file_path: str,
        upload_type: str,
        total_ae_files: int,
        total_cp_files: int,
        year: int,
        source_region: str,
        username: str,
        client_id: Optional[str] = None,
    ) -> SessionState:
        """Enregistre un fichier uploadé dans la session courante."""
        self._ensure_lock_is_active()

        if self._state is None:
            self._state = SessionState(
                session_token=self.id,
                total_ae_files=total_ae_files,
                total_cp_files=total_cp_files,
                year=year,
                source_region=source_region,
                username=username,
                client_id=client_id,
            )
            logger.info(f"Created new session state for {self.id}")

        file_hash = self._service._calculate_file_hash(file_path)
        logger.info(f"Calculated hash for {file_path}: {file_hash}")

        temp_folder = self._service._get_session_temp_folder(self.id)
        filename = os.path.basename(file_path)
        file_index = self._state.total_received + 1
        unique_filename = f"{file_index:03d}_{upload_type}_{filename}"
        temp_path = temp_folder / unique_filename

        shutil.move(file_path, temp_path)
        logger.info(f"Moved file to {temp_path}")

        self._state.file_hashes[str(temp_path)] = file_hash

        if upload_type == UploadType.FINANCIAL_AE.value:
            self._state.received_ae_files.append(str(temp_path))
            self._state.original_ae_filenames.append(filename)
        elif upload_type == UploadType.FINANCIAL_CP.value:
            self._state.received_cp_files.append(str(temp_path))
            self._state.original_cp_filenames.append(filename)
        else:
            raise ValueError(f"Unsupported upload type: {upload_type}")

        logger.info(f"Session {self.id}: {self._state.total_received}/{self._state.total_expected} files received")
        self._service._save_session_state(self._state)
        return self._state

    def finalize(self) -> tuple[str, str]:
        """Finalise la session courante en concaténant les fichiers attendus."""
        self._ensure_lock_is_active()

        if self._state is None:
            raise ValueError(f"Session {self.id} not found")

        if not self._state.is_complete:
            raise ValueError(
                f"Session {self.id} is not complete: {self._state.total_received}/{self._state.total_expected} files received"
            )

        ae_first_filename = (
            self._service._extract_base_filename(self._state.original_ae_filenames[0])
            if self._state.original_ae_filenames
            else "unknown"
        )
        cp_first_filename = (
            self._service._extract_base_filename(self._state.original_cp_filenames[0])
            if self._state.original_cp_filenames
            else "unknown"
        )

        ae_output = (
            self._service.final_folder
            / f"{ae_first_filename}_{len(self._state.received_ae_files)}_AE_{self._state.year}.csv"
        )
        cp_output = (
            self._service.final_folder
            / f"{cp_first_filename}_{len(self._state.received_cp_files)}_CP_{self._state.year}.csv"
        )

        ae_final_path = self._service.concatenate_csv_files(self._state.received_ae_files, ae_output)
        cp_final_path = self._service.concatenate_csv_files(self._state.received_cp_files, cp_output)

        self._state.final_ae_file = ae_final_path
        self._state.final_cp_file = cp_final_path
        self._service._save_session_state(self._state)

        logger.info(f"Session {self.id} finalized: AE={ae_final_path}, CP={cp_final_path}")
        return ae_final_path, cp_final_path


class UploadSessionService:
    """Service de gestion des sessions d'upload multi-fichiers"""

    def __init__(
        self,
        sessions_folder: str,
        final_folder: str,
        db_session_factory: Callable[[], Any],
        session_lock_timeout_seconds: float = 10.0,
        session_lock_retry_interval_seconds: float = 0.05,
    ):
        """
        Initialise le service.

        Args:
            sessions_folder: Dossier pour stocker les états de session (fichiers JSON)
            final_folder: Dossier final pour les fichiers concaténés
            db_session_factory: Callable retournant une session SQLAlchemy dédiée
        """
        self.sessions_folder = Path(sessions_folder)
        self.final_folder = Path(final_folder)
        self.db_session_factory = db_session_factory
        self.session_lock_timeout_seconds = session_lock_timeout_seconds
        self.session_lock_retry_interval_seconds = session_lock_retry_interval_seconds

        # Créer les dossiers si nécessaire
        self.sessions_folder.mkdir(parents=True, exist_ok=True)
        self.final_folder.mkdir(parents=True, exist_ok=True)

    def _get_session_file(self, session_token: str) -> Path:
        """Retourne le chemin du fichier de session"""
        return self.sessions_folder / f"{session_token}.json"

    def _get_session_temp_folder(self, session_token: str) -> Path:
        """Retourne le dossier temporaire pour les fichiers de la session"""
        folder = self.sessions_folder / session_token
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def _extract_base_filename(self, filename: str) -> str:
        """Extrait le nom de base d'un fichier sans extension.

        Args:
            filename: Nom du fichier (ex: "fichier_data.csv")

        Returns:
            Nom sans extension (ex: "fichier_data")
        """
        return Path(filename).stem

    def get_session_state(self, session_token: str) -> Optional[SessionState]:
        """Récupère l'état d'une session si elle existe"""
        session_file = self._get_session_file(session_token)
        if session_file.exists():
            with open(session_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                return SessionState.from_dict(data)
        return None

    @contextmanager
    def borrow_session(self, session_token: str) -> Iterator[UploadSession]:
        """Emprunte une session sous verrou PostgreSQL advisory exclusif."""
        lock_key = PgAdvisoryLock.token_to_lock_key(session_token)
        with PgAdvisoryLock(
            self.db_session_factory,
            lock_key,
            timeout_seconds=self.session_lock_timeout_seconds,
            retry_interval_seconds=self.session_lock_retry_interval_seconds,
        ) as lock:
            yield UploadSession(self, session_token, lock, self.get_session_state(session_token))

    def _save_session_state(self, state: SessionState) -> None:
        """Sauvegarde l'état de la session"""
        session_file = self._get_session_file(state.session_token)
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2)

    def _calculate_file_hash(self, file_path: str) -> str:
        """Calcule le hash SHA256 d'un fichier.

        Args:
            file_path: Chemin du fichier

        Returns:
            Hash SHA256 en hexadécimal
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Lire le fichier par blocs pour économiser la mémoire
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def concatenate_csv_files(self, files: list[str], output_path: Path) -> str:
        """
        Concatène plusieurs fichiers CSV en un seul.

        Le header est conservé uniquement du premier fichier.
        Les fichiers suivants sont ajoutés sans leur première ligne (header).

        Args:
            files: Liste des chemins de fichiers à concaténer
            output_path: Chemin du fichier de sortie

        Returns:
            Chemin du fichier concaténé
        """
        if not files:
            raise ValueError("No files to concatenate")

        # Trier les fichiers pour garantir un ordre déterministe
        sorted_files = sorted(files)

        logger.info(f"Concatenating {len(sorted_files)} files to {output_path}")

        with open(output_path, "w", encoding="utf-8", newline="") as outfile:
            for i, file_path in enumerate(sorted_files):
                with open(file_path, "r", encoding="utf-8") as infile:
                    lines = infile.readlines()
                    if i == 0:
                        # Premier fichier : garder le header
                        outfile.writelines(lines)
                    else:
                        # Fichiers suivants : sauter le header (première ligne)
                        if lines:
                            outfile.writelines(lines[1:])

        logger.info(f"Successfully concatenated files to {output_path}")
        return str(output_path)
