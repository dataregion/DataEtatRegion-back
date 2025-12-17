from batches.share.tabular_writer.abstract import TabularWriter


import csv


class CsvTabularWriter(TabularWriter):
    def __init__(self, filep: str, username: str | None = None) -> None:
        super().__init__(filep, username)

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
