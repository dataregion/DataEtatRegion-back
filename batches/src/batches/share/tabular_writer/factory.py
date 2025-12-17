from models.value_objects.export_api import ExportTarget
from batches.share.tabular_writer.abstract import TabularWriter
from batches.share.tabular_writer.csv import CsvTabularWriter
from batches.share.tabular_writer.excel import ExcelTabularWriter
from batches.share.tabular_writer.grist import GristTabularWriter
from batches.share.tabular_writer.ods import OdsTabularWriter

class TabularWriterFactory:
    @staticmethod
    def create_writer(filep: str, export_target: ExportTarget, username: str | None) -> TabularWriter:
        if export_target == "csv":
            return CsvTabularWriter(filep, username)
        if export_target == "to-grist":
            return GristTabularWriter(filep, username)
        if export_target == 'xlsx':
            return ExcelTabularWriter(filep, username)
        if export_target == 'ods':
            return OdsTabularWriter(filep, username)
        raise NotImplementedError()