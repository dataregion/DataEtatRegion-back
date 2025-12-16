from abc import ABC, abstractmethod
import csv
from models.value_objects.export_api import ExportTarget


class TabularWriter(ABC):
    def __init__(self, filep: str) -> None:
        self._filep = filep
        pass

    @abstractmethod
    def write_header(self, header: list[str]) -> None:
        raise NotImplementedError("Not implemented yet")

    @abstractmethod
    def write_rows(self, rows: list) -> None:
        raise NotImplementedError("Not implemented yet")

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError("Not implemented yet")

    @staticmethod
    def create_writer(filep: str, export_target: ExportTarget) -> "TabularWriter":
        if export_target == "csv":
            return CsvTabularWriter(filep)
        raise NotImplementedError()


class StubTabularWriter(TabularWriter):
    def write_header(self, header: list[str]) -> None:
        print(f"StubTabularWriter.write_header: {header}")

    def write_rows(self, rows: list) -> None:
        print(f"StubTabularWriter.write_rows: {len(rows)} rows")

    def close(self) -> None:
        print("StubTabularWriter.close")


class CsvTabularWriter(TabularWriter):
    def write_header(self, header: list[str]) -> None:
        print(f"CsvTabularWriter.write_header: {header}")
        with open(self._filep, "a", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(header)

    def write_rows(self, rows: list) -> None:
        print(f"CsvTabularWriter.write_rows: {len(rows)} rows")
        with open(self._filep, "a", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerows(rows)

    def close(self) -> None:
        print("CsvTabularWriter.close")
