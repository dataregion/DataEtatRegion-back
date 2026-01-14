from sqlalchemy import select
from sqlalchemy.orm import Session

from models.entities.audit.RemoteFile import RemoteFile


class RemoteFileService:

    @staticmethod
    def find_by_resource_uuid(session: Session, resource_uuid: str) -> RemoteFile | None:
        stmt = (
            select(RemoteFile)
            .where(RemoteFile.resource_uuid == resource_uuid)
        )
        return session.execute(stmt).scalar_one_or_none()
