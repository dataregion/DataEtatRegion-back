from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from prefect import task
from prefect.cache_policies import NO_CACHE
import requests
from services.audits.remote_file import RemoteFileService
from sqlalchemy.dialects.postgresql import insert
import tempfile
from typing import Literal, Optional

from models.entities.audit.RemoteFile import RemoteFile
from batches.database import session_audit_scope


Downloadable = Literal["csv", "zip"]


def _print(text: str):
    print(f"[TASK][FILE_UTILS] {text}")


@dataclass
class CtxDownloadFile:
    task_name: str
    url: str
    resource_uuid: str

    filename: Optional[str] = None
    extension: Optional[Downloadable] = None
    db_fingerprint: Optional[RemoteFile] = None
    should_download: bool = True  # Par défaut, on télécharge


@task(timeout_seconds=60, log_prints=True, cache_policy=NO_CACHE)
def should_download(ctx: CtxDownloadFile) -> CtxDownloadFile:
    """
    Détermine si un fichier distant doit être téléchargé à nouveau
    en comparant Last-Modified et Content-Length avec le fingerprint en base.
    """
    _print(f"Vérification du fichier distant pour {ctx.task_name}")

    try:
        response = requests.get(ctx.url, stream=True, allow_redirects=True, timeout=30)
        response.raise_for_status()
        headers = response.headers
    finally:
        response.close()

    last_modified_raw = headers.get("Last-Modified")
    content_length_raw = headers.get("Content-Length")
    last_modified = parsedate_to_datetime(last_modified_raw) if last_modified_raw else None
    content_length = int(content_length_raw) if content_length_raw else None

    _print(f"Last-Modified : {last_modified}")
    _print(f"Content-Length : {content_length}")

    with session_audit_scope() as session:
        # Recherche fingerprint existant
        remote_file: RemoteFile | None = RemoteFileService.find_by_resource_uuid(session, ctx.resource_uuid)
        if (
            remote_file
            and last_modified
            and content_length
            and remote_file.last_modified == last_modified
            and remote_file.content_length == content_length
        ):
            ctx.should_download = False
            ctx.db_fingerprint = remote_file
            _print("Fichier inchangé : pas de téléchargement")
            return ctx

        if remote_file:
            _print("Fichier modifié : téléchargement requis")
        else:
            _print("Fichier inconnu : premier téléchargement")

        stmt = (
            insert(RemoteFile)
            .values(
                name=ctx.task_name,
                resource_uuid=ctx.resource_uuid,
                last_modified=last_modified,
                content_length=content_length,
            )
            .on_conflict_do_update(
                index_elements=[RemoteFile.resource_uuid],
                set_={
                    "name": ctx.task_name,
                    "last_modified": last_modified,
                    "content_length": content_length,
                },
            )
            .returning(RemoteFile)
        )
        remote_file = session.execute(stmt).scalar_one()
        ctx.db_fingerprint = remote_file

    ctx.should_download = True
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
    _print(f"Téléchargement du fichier pour la tâche : {ctx.task_name}")
    response = requests.get(ctx.url, stream=True)
    response.raise_for_status()

    content_type = response.headers.get("Content-Type", "").lower()

    with tempfile.NamedTemporaryFile(delete=False) as temp_file:
        for chunk in response.iter_content(chunk_size=1024):
            if chunk:
                temp_file.write(chunk)

        ctx.filename = temp_file.name
        _print("Fichier téléchargé.")

        if "zip" in content_type:
            ctx.extension = "zip"
        elif "csv" in content_type:
            ctx.extension = "csv"
        else:
            raise RuntimeError(f"Type de fichier non géré pour le téléchargement : {content_type}")

    return ctx
