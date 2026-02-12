from models.value_objects.export_api import ExportTarget
from batches.share.tabular_writer.abstract import TabularWriter
from batches.share.tabular_writer.csv import CsvTabularWriter
from batches.share.tabular_writer.grist import GristTabularWriter


class TabularWriterFactory:
    @staticmethod
    def create_writer(filep: str, export_target: ExportTarget, username: str | None) -> TabularWriter:
        if export_target == "csv":
            return CsvTabularWriter(filep, username)
        if export_target == "to-grist":
            return GristTabularWriter(filep, username)
        if export_target in ["xlsx", "ods"]:
            raise ValueError(
                f"Les writers directs pour '{export_target}' ont été supprimés pour des raisons de performance. "
                "Utilisez le writer CSV puis convertissez via le module converter."
            )
        raise NotImplementedError(f"Format non supporté: {export_target}")
