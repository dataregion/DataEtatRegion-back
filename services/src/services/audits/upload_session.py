"""
Service de gestion des sessions d'upload multi-fichiers.

Ce service permet de :
- Tracker les fichiers reçus par session_token
- Détecter quand tous les fichiers d'une session sont reçus
- Concaténer les fichiers CSV AE et CP en fichiers uniques
"""

import json
import logging
import os
import shutil
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional

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


class UploadSessionService:
    """Service de gestion des sessions d'upload multi-fichiers"""

    def __init__(self, sessions_folder: str, final_folder: str):
        """
        Initialise le service.

        Args:
            sessions_folder: Dossier pour stocker les états de session (fichiers JSON)
            final_folder: Dossier final pour les fichiers concaténés
        """
        self.sessions_folder = Path(sessions_folder)
        self.final_folder = Path(final_folder)

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

    def _save_session_state(self, state: SessionState) -> None:
        """Sauvegarde l'état de la session"""
        session_file = self._get_session_file(state.session_token)
        with open(session_file, "w", encoding="utf-8") as f:
            json.dump(state.to_dict(), f, indent=2)

    def register_file(
        self,
        file_path: str,
        session_token: str,
        upload_type: str,
        total_ae_files: int,
        total_cp_files: int,
        year: int,
        source_region: str,
        username: str,
        client_id: Optional[str] = None,
    ) -> SessionState:
        """
        Enregistre un fichier uploadé dans la session.

        Args:
            file_path: Chemin du fichier uploadé
            session_token: Token de session unique
            upload_type: Type d'upload (financial-ae ou financial-cp)
            total_ae_files: Nombre total de fichiers AE attendus
            total_cp_files: Nombre total de fichiers CP attendus
            year: Année des données
            source_region: Région source
            username: Email de l'utilisateur
            client_id: ID client de l'application (optionnel)

        Returns:
            État mis à jour de la session
        """
        # Récupérer ou créer l'état de la session
        state = self.get_session_state(session_token)
        if state is None:
            state = SessionState(
                session_token=session_token,
                total_ae_files=total_ae_files,
                total_cp_files=total_cp_files,
                year=year,
                source_region=source_region,
                username=username,
                client_id=client_id,
            )
            logger.info(f"Created new session state for {session_token}")

        # Copier le fichier dans le dossier temporaire de la session
        temp_folder = self._get_session_temp_folder(session_token)
        filename = os.path.basename(file_path)

        # Ajouter un préfixe unique pour éviter les collisions de noms
        file_index = state.total_received + 1
        unique_filename = f"{file_index:03d}_{upload_type}_{filename}"
        temp_path = temp_folder / unique_filename

        shutil.move(file_path, temp_path)
        logger.info(f"Moved file to {temp_path}")

        # Enregistrer le fichier dans la liste appropriée
        if upload_type == UploadType.FINANCIAL_AE.value:
            state.received_ae_files.append(str(temp_path))
            state.original_ae_filenames.append(filename)
        elif upload_type == UploadType.FINANCIAL_CP.value:
            state.received_cp_files.append(str(temp_path))
            state.original_cp_filenames.append(filename)

        logger.info(f"Session {session_token}: {state.total_received}/{state.total_expected} files received")

        # Sauvegarder l'état
        self._save_session_state(state)

        return state

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

    def finalize_session(self, session_token: str) -> tuple[str, str]:
        """
        Finalise une session complète en concaténant les fichiers.

        Args:
            session_token: Token de session

        Returns:
            Tuple (chemin_fichier_ae_concaténé, chemin_fichier_cp_concaténé)

        Raises:
            ValueError: Si la session n'est pas complète
        """
        state = self.get_session_state(session_token)
        if state is None:
            raise ValueError(f"Session {session_token} not found")

        if not state.is_complete:
            raise ValueError(
                f"Session {session_token} is not complete: {state.total_received}/{state.total_expected} files received"
            )

        # Générer les noms de fichiers concaténés
        # Format: {nom_premier_fichier_sans_extension}_{nb_fichiers}_{TYPE}_{année}.csv
        ae_first_filename = (
            self._extract_base_filename(state.original_ae_filenames[0]) if state.original_ae_filenames else "unknown"
        )
        cp_first_filename = (
            self._extract_base_filename(state.original_cp_filenames[0]) if state.original_cp_filenames else "unknown"
        )

        ae_output = self.final_folder / f"{ae_first_filename}_{len(state.received_ae_files)}_AE_{state.year}.csv"
        cp_output = self.final_folder / f"{cp_first_filename}_{len(state.received_cp_files)}_CP_{state.year}.csv"

        # Concaténer les fichiers AE
        ae_final_path = self.concatenate_csv_files(state.received_ae_files, ae_output)

        # Concaténer les fichiers CP
        cp_final_path = self.concatenate_csv_files(state.received_cp_files, cp_output)

        logger.info(f"Session {session_token} finalized: AE={ae_final_path}, CP={cp_final_path}")

        return ae_final_path, cp_final_path

    def cleanup_session(self, session_token: str) -> None:
        """
        Nettoie les fichiers temporaires d'une session.

        Args:
            session_token: Token de session
        """
        # Supprimer le dossier temporaire
        temp_folder = self._get_session_temp_folder(session_token)
        if temp_folder.exists():
            shutil.rmtree(temp_folder)
            logger.info(f"Cleaned up temp folder for session {session_token}")

        # Supprimer le fichier de session
        session_file = self._get_session_file(session_token)
        if session_file.exists():
            session_file.unlink()
            logger.info(f"Cleaned up session file for {session_token}")
