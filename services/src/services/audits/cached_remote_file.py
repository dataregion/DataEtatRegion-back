from sqlalchemy import select
from sqlalchemy.orm import Session

from models.entities.audit.CachedRemoteFile import CachedRemoteFile


class CachedRemoteFileService:
    @staticmethod
    def find_by_resource_url(session: Session, resource_url: str) -> CachedRemoteFile | None:
        stmt = select(CachedRemoteFile).where(CachedRemoteFile.resource_url == resource_url)
        return session.execute(stmt).scalar_one_or_none()
