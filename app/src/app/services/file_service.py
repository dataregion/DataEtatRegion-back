import os
import tempfile
from pathlib import Path
import logging
from datetime import datetime


from werkzeug.utils import secure_filename

from flask import current_app
from app.exceptions.exceptions import InvalidFile, FileNotAllowedException
from app.services import FileStorageProtocol
from services.antivirus import AntivirusService, AntivirusError, VirusFoundError

logger = logging.getLogger(__name__)


def allowed_file(filename, allowed_extensions=None) -> bool:
    """
    Vérifie que le nom de fichier a une extension autorisée par
    :param allowed_extensions: dictionnaire d'extensions autorisées.
    """
    if allowed_extensions is None:
        allowed_extensions = {"csv"}

    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def check_file_and_save(file: FileStorageProtocol, allowed_extensions=None, in_unique_folder=False) -> str:
    """
    Vérifie l'extension du fichier, le sauvegarde dans le `UPLOAD_FOLDER` puis le scanne
    avec l'antivirus (si activé). En cas de virus ou d'erreur antivirus, le fichier est
    supprimé et une exception `InvalidFile` est levée (politique fail-closed).

    Si le `UPLOAD_FOLDER` n'est pas spécifié, le fichier est déplacé dans un dossier temporaire.

    :return: chemin posix du fichier sauvegardé
    """
    if file.filename == "":
        raise InvalidFile(message="Pas de fichier")

    _check_file_extension(file, allowed_extensions=allowed_extensions)

    if not file:
        logger.error("[IMPORT] Fichier refusé %s", file.filename)
        raise FileNotAllowedException(message=f"le fichier n'est pas au format {allowed_extensions}")

    filename = file.filename or f"unknown.{_timestamp_str()}"
    filename = secure_filename(filename)

    save_path = _upload_folder_path(using_unique_intermediate_folder=in_unique_folder) / filename
    file.save(save_path)

    scan_av_and_reject_on_error(file_path=save_path, filename=filename)

    return save_path.as_posix()


def _upload_folder_path(using_unique_intermediate_folder=False) -> Path:
    """
    Retourne un chemin vers l'upload folder.
    Si la clef de configuration "UPLOAD_FOLDER" n'est pas définit, retourne un dossier temporaire.

    :param using_unique_intermediate_folder: Si vrai, suffixe le chemin avec un nom de dossier unique.
    """
    if "UPLOAD_FOLDER" in current_app.config:
        save_path = os.path.join(current_app.config["UPLOAD_FOLDER"])
    else:
        save_path = os.path.join(tempfile.gettempdir())

    if using_unique_intermediate_folder:
        unique_folder_name = tempfile.mkdtemp(dir=save_path, prefix="unique_")
        save_path = unique_folder_name

    return Path(save_path)


def _check_file_extension(file: FileStorageProtocol, allowed_extensions=None):
    """
    Vérifie que l'extension du fichier est légale
    :raises FileNotAllowedException:
        Si l'extension est illégale
    """
    if not allowed_file(file.filename, allowed_extensions=allowed_extensions):
        logger.error("[IMPORT] Fichier refusé %s", file.filename)
        raise FileNotAllowedException(message=f"Le fichier n'a pas l'extension requise ({allowed_extensions})")


def _timestamp_str():
    return str(int(datetime.timestamp(datetime.now())))


def scan_av_and_reject_on_error(file_path: Path, filename: str) -> None:
    """Scanne le fichier avec ClamAV et lève InvalidFile en cas de problème (fail-closed).

    Si l'antivirus est désactivé ou non configuré, le scan est ignoré avec un avertissement.
    En cas de virus détecté ou d'erreur antivirus, le fichier est supprimé avant de lever l'exception.
    """
    av_config = current_app.config.get("ANTIVIRUS")
    if not av_config or not av_config.get("ENABLED", False):
        logger.warning("[ANTIVIRUS] Scan désactivé ou non configuré [filename=%s]", filename)
        return

    av_service = AntivirusService(
        host=av_config["HOST"],
        port=av_config["PORT"],
        timeout=av_config.get("TIMEOUT", 60),
        max_file_size_bytes=av_config.get("MAX_FILE_SIZE_BYTES", 25 * 1024 * 1024),
    )

    try:
        av_service.scan_file(
            file_path=str(file_path),
            context={"filename": filename},
        )
    except AntivirusError as e:
        _delete_file_silently(file_path, filename=filename)
        if isinstance(e, VirusFoundError):
            raise InvalidFile(
                name="VirusFound",
                message="Le fichier a été rejeté car il contient un virus.",
            )
        raise InvalidFile(
            name="AntivirusScanFailed",
            message="Le fichier a été rejeté car le contrôle antivirus a échoué.",
        )


def _delete_file_silently(file_path: Path, *, filename: str) -> None:
    """Tente de supprimer le fichier en loggant toute erreur sans la propager."""
    try:
        os.remove(file_path)
        logger.info("[ANTIVIRUS] Fichier supprimé après échec du scan [filename=%s]", filename)
    except Exception as delete_err:
        logger.error(
            "[ANTIVIRUS] Impossible de supprimer le fichier après échec du scan [filename=%s]",
            filename,
            exc_info=delete_err,
        )
