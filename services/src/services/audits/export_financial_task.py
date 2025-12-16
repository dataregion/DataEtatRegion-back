from sqlalchemy import select, desc
from sqlalchemy.orm import Session

from models.entities.audit.ExportFinancialTask import ExportFinancialTask
import datetime

from models.value_objects.export_api import ExportTarget


class ExportFinancialTaskService:
    @staticmethod
    def find_by_run_id(session: Session, run_id: str):
        stmt = (
            select(ExportFinancialTask)
            .where(ExportFinancialTask.prefect_run_id == run_id)
            .order_by(ExportFinancialTask.id.desc())
        )
        return session.execute(stmt).scalar_one()

    @staticmethod
    def find_all_by_username(session: Session, username: str):
        stmt = (
            select(ExportFinancialTask)
            .where(ExportFinancialTask.username == username)
            .order_by(desc(ExportFinancialTask.created_at))
        )
        return session.execute(stmt).scalars().all()

    @staticmethod
    def initialize_and_persist_export_task_entity(
        session: Session, username: str, prefect_id: str, name: str, format: ExportTarget = "csv"
    ) -> ExportFinancialTask:
        """Initialise une entité d'export financier en mode upsert et la persiste."""

        export = (
            session.query(ExportFinancialTask).filter(ExportFinancialTask.prefect_run_id == prefect_id).one_or_none()
        )
        if export is None:
            export = ExportFinancialTask.create(username=username, prefect_id=prefect_id, name=name)
            session.add(export)

        export.name = name
        export.username = username
        export.prefect_run_id = prefect_id
        export.status = "PENDING"
        export.started_at = datetime.datetime.now(datetime.UTC)
        export.target_format = format

        session.commit()
        session.refresh(export)
        return export

    @staticmethod
    def complete_export_task_entity(session: Session, task_id: int, file_path: str) -> ExportFinancialTask:
        """Complète la tâche d'export financier une fois le fichier généré."""
        export = session.query(ExportFinancialTask).filter(ExportFinancialTask.id == task_id).one()

        export.file_path = file_path
        export.status = "DONE"
        export.completed_at = datetime.datetime.now(datetime.UTC)

        session.commit()
        session.refresh(export)
        return export
