from models import _PersistenceBaseModelInstance
from sqlalchemy import Boolean, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column


class _SyncedWithGrist(_PersistenceBaseModelInstance()):
    __abstract__ = True
    synchro_grist_id: Mapped[int] = mapped_column(ForeignKey("synchro_grist.id"), nullable=True)
    grist_row_id: Mapped[int] = mapped_column(Integer, unique=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False, server_default="FALSE")
