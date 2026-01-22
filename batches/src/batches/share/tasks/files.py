from dataclasses import dataclass
from datetime import datetime
from email.utils import parsedate_to_datetime
import os
from prefect import task
from prefect.cache_policies import NO_CACHE
import requests
from services.audits.cached_remote_file import CachedRemoteFileService
from sqlalchemy.dialects.postgresql import insert
from typing import Literal, Optional, get_args

from models.entities.audit.CachedRemoteFile import CachedRemoteFile
from batches.config.current import get_config  # noqa: E402
from batches.database import session_audit_scope


Downloadable = Literal["csv", "zip"]


DOWNLOAD_DIR = get_config().dossier_des_telechargements


def _print(text: str):
    print(f"[TASK][FILE_UTILS] {text}")


@dataclass
class CtxDownloadFile:
    name: str
    resource_url: str

    should_download: bool = True
    file_path: Optional[str] = None
    new_last_modified: Optional[datetime] = None
    new_content_length: Optional[int] = None


@task(log_prints=True, cache_policy=NO_CACHE)
def download_or_get_file(ctx: CtxDownloadFile) -> CtxDownloadFile:
    """
    Check l'existence dans le cache d'u fichier distant à récupérer
    S'il existe on le retourne, sinon on le télécharge
    """
    ctx = should_download(ctx)
    if ctx.should_download:
        ctx = download_remote_file(ctx)
    return ctx


@task(timeout_seconds=60, log_prints=True, cache_policy=NO_CACHE)
def should_download(ctx: CtxDownloadFile) -> CtxDownloadFile:
    """
    Détermine si un fichier distant doit être téléchargé à nouveau
    en comparant Last-Modified et Content-Length avec le fingerprint en base.
    """
    _print(f"Vérification du fichier distant pour {ctx.name}")

    response = requests.head(ctx.resource_url, allow_redirects=True, timeout=30)
    response.raise_for_status()
    headers = response.headers

    last_modified_raw = headers.get("Last-Modified")
    content_length_raw = headers.get("Content-Length")
    ctx.new_last_modified = parsedate_to_datetime(last_modified_raw) if last_modified_raw else None
    ctx.new_content_length = int(content_length_raw) if content_length_raw else None

    _print(f"Last-Modified : {ctx.new_last_modified}")
    _print(f"Content-Length : {ctx.new_content_length}")

    with session_audit_scope() as session:
        # Recherche fingerprint existant
        remote_file: CachedRemoteFile | None = CachedRemoteFileService.find_by_resource_url(session, ctx.resource_url)
        if (
            remote_file
            and ctx.new_last_modified
            and ctx.new_content_length
            and remote_file.last_modified == ctx.new_last_modified
            and remote_file.content_length == ctx.new_content_length
            and os.path.exists(remote_file.file_path)
        ):
            ctx.should_download = False
            ctx.file_path = remote_file.file_path
            _print("Fichier inchangé : pas de téléchargement")
            return ctx

        ctx.should_download = True

        if remote_file:
            if os.path.exists(remote_file.file_path):
                _print("Fichier introuvable : on télécharge")
            else:
                _print("Fichier modifié : on télécharge")
        else:
            _print("Cache de fichier invalide : on télécharge")

    return ctx


@task(log_prints=True, cache_policy=NO_CACHE)
def download_remote_file(ctx: CtxDownloadFile) -> CtxDownloadFile:
    """
    Fais une requête GET et télécharge dans un fichier temporaire.
    Détermine automatiquement l'extension du fichier.

    :param ctx: Contexte lié au téléchargement du fichier
    :type ctx: CtxDownloadFile
    :return: Contexte mis à jour
    :rtype: CtxDownloadFile
    """
    _print(f"Téléchargement du fichier pour la tâche : {ctx.name}")
    response = requests.get(ctx.resource_url, stream=True)
    response.raise_for_status()

    _print(f"Vérification de l'extension, types gérés : {','.join(get_args(Downloadable))}")
    content_type = response.headers.get("Content-Type", "").lower()
    extension: Optional[Downloadable] = None
    if "zip" in content_type:
        extension = "zip"
    elif "csv" in content_type:
        extension = "csv"
    else:
        raise RuntimeError(f"Type de fichier non géré pour le téléchargement : {content_type}")

    filename = f"{ctx.name}.{extension}"
    target_path = DOWNLOAD_DIR / filename

    if not os.path.exists(DOWNLOAD_DIR):
        os.mkdir(DOWNLOAD_DIR)

    _print(f"Début du téléchargement : {target_path}")
    with open(target_path, "wb+") as file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                file.write(chunk)
        _print(f"Fichier téléchargé : {target_path}")

    _print("Mise à jour en BDD du cached_remote_file...")
    with session_audit_scope() as session:
        stmt = (
            insert(CachedRemoteFile)
            .values(
                name=ctx.name,
                resource_url=ctx.resource_url,
                file_path=str(target_path),
                last_modified=ctx.new_last_modified,
                content_length=ctx.new_content_length,
            )
            .on_conflict_do_update(
                index_elements=[CachedRemoteFile.resource_url],
                set_={
                    "last_modified": ctx.new_last_modified,
                    "content_length": ctx.new_content_length,
                },
            )
            .returning(CachedRemoteFile)
        )
        remote_file = session.execute(stmt).scalar_one()
        ctx.file_path = remote_file.file_path

    return ctx
