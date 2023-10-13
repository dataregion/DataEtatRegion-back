import logging
import sqlparse

import celery


class SAFormatter(logging.Formatter):
    def format(self, record):
        if "sqlalchemy.engine" in record.name and record.msg:
            formatted = sqlparse.format(record.msg, reindent=True, keyword_case="upper")
            record.msg = "\n"
            record.msg += formatted

        return super().format(record)


def setup():
    format = "%(levelname)s:%(name)s:%(message)s"
    formatter = SAFormatter(fmt=format)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    sa_logger = logging.getLogger("sqlalchemy.engine")
    sa_logger.addHandler(ch)
    sa_logger.setLevel(logging.INFO)
    sa_logger.propagate = False  # XXX: important to prevent double logging of sql requests
