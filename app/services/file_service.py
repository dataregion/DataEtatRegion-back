import os
import tempfile
from pathlib import Path
import logging
from datetime import datetime


from werkzeug.utils import secure_filename
from werkzeug.datastructures import FileStorage

from flask import current_app
from app.exceptions.exceptions import InvalidFile, FileNotAllowedException


def allowed_file(filename, allowed_extensions=None) -> bool:
    """
    Vérifie que le nom de fichier a une extension autorisée par
    :param allowed_extensions: dictionnaire d'extensions autorisées.
    """
    if allowed_extensions is None:
        allowed_extensions = {"csv"}

    return "." in filename and filename.rsplit(".", 1)[1].lower() in allowed_extensions


def check_file_and_save(file, allowed_extensions=None, in_unique_folder=False) -> str:
    """
    Vérifie l'extension du fichier
    et le sauvegarde dans le `UPLOAD_FOLDER`. Si le `UPLOAD_FOLDER` n'est pas spécifié, le déplace dans un dossier temporaire.

    :return: chemin posix du fichier sauvegardé
    """
    if file.filename == "":
        raise InvalidFile(message="Pas de fichier")

    _check_file_extension(file)

    if not file:
        logging.error(f"[IMPORT] Fichier refusé {file.filename}")
        raise FileNotAllowedException(message=f"le fichier n'est pas au format {allowed_extensions}")

    filename = file.filename or f"unknown.{_timestamp_str()}"
    filename = secure_filename(filename)

    save_path = _upload_folder_path(using_unique_intermediate_folder=in_unique_folder) / filename
    file.save(save_path)

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


def _check_file_extension(file: FileStorage, allowed_extensions=None):
    """
    Vérifie que l'extension du fichier est légale
    :raises FileNotAllowedException:
        Si l'extension est illégale
    """
    if not allowed_file(file.filename):
        logging.error(f"[IMPORT] Fichier refusé {file.filename}")
        raise FileNotAllowedException(message=f"Le fichier n'a pas l'extension requise ({allowed_extensions})")


def _timestamp_str():
    return str(int(datetime.timestamp(datetime.now())))
