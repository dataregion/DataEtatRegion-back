"""
Configure pretty printing capabilities for sqlalchemy logger
"""

import logging
import sqlparse


class SAFormatter(logging.Formatter):
    def format(self, record):
        if "sqlalchemy.engine" in record.name and record.msg:
            formatted = sqlparse.format(record.msg, reindent=True, keyword_case="upper")
            record.msg = "\n"
            record.msg += formatted

        return super().format(record)


def setup(format: str | None = None, level=None):
    """
    Setup a pretty printer formatter to stdout for sqlachemy.engine logger.
    XXX: it optionally setup the logger level. If not specified it will not log since sqlalchemy.engine default level is WARNING
    """
    if format is None:
        format = "%(levelname)s:%(name)s:%(message)s"

    formatter = SAFormatter(fmt=format)
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)

    sa_logger = logging.getLogger("sqlalchemy.engine")
    sa_logger.addHandler(ch)
    if level is not None:
        sa_logger.setLevel(level)
    sa_logger.propagate = False  # XXX: important to prevent double logging of sql requests
