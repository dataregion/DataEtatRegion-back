import logging
from collections import namedtuple

LineImportTechInfo = namedtuple('LineImportTechInfo', ['file_import_taskid', 'lineno'])


logger = logging.getLogger(__name__)
logger.setLevel(level = logging.DEBUG)