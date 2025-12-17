from abc import ABC, abstractmethod


class TabularWriter(ABC):
    def __init__(self, filep: str, username: str | None = None) -> None:
        self._filep = filep
        self._username = username

    @abstractmethod
    def write_header(self, header: list[str]) -> None:
        pass

    @abstractmethod
    def write_rows(self, rows: list) -> None:
        pass

    @abstractmethod
    def close(self) -> None:
        pass



class StubTabularWriter(TabularWriter):
    def write_header(self, header: list[str]) -> None:
        print(f"StubTabularWriter.write_header: {header}")

    def write_rows(self, rows: list) -> None:
        print(f"StubTabularWriter.write_rows: {len(rows)} rows")

    def close(self) -> None:
        print("StubTabularWriter.close")