"""
Module utilitaire pour visu territoire
TODO: à déplacer dans les services post merge de megarequetes
"""

import hashlib
import struct
from sqlalchemy.orm import Session
from sqlalchemy import text
from contextlib import contextmanager


class AdvisoryLockError(Exception):
    """Erreur lorsque l'advisory lock est vérouillé"""

    pass


def advisory_lock_id_from_str(s: str) -> tuple[int, int]:
    h = hashlib.sha256(s.encode("utf-8")).digest()
    key1, key2 = struct.unpack(">ii", h[:8])  # ">ii" = big-endian, 2 int32
    return key1, key2


@contextmanager
def try_advisory_lock(session: Session, key: str):
    sql = text("SELECT pg_try_advisory_lock(:key1, :key2);")
    key1, key2 = advisory_lock_id_from_str(key)
    result = session.execute(sql, {"key1": key1, "key2": key2})
    if not result.scalar():
        raise AdvisoryLockError()

    try:
        yield
    finally:
        sql = text("SELECT pg_advisory_unlock(:key1, :key2)")
        session.execute(sql, {"key1": key1, "key2": key2})
