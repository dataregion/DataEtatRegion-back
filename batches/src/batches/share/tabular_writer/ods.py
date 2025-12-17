from odf import opendocument
from odf.table import Table, TableRow, TableCell
from odf.text import P
import os

from batches.share.tabular_writer.abstract import TabularWriter

class OdsTabularWriter(TabularWriter):

    def __init__(self, filep: str, username: str | None = None) -> None:
        super().__init__(filep, username)

    def write_header(self, header: list[str]) -> None:
        print(f"OdsTabularWriter.write_header: {header}")
        
        doc = opendocument.OpenDocumentSpreadsheet()
        
        table = Table(name="Sheet1")
        
        row = TableRow()
        for cell_value in header:
            cell = TableCell()
            cell.addElement(P(text=str(cell_value)))
            row.addElement(cell)
        table.addElement(row)
        
        doc.spreadsheet.addElement(table)
        
        # Sauvegarder
        doc.save(self._filep)

    def write_rows(self, rows: list) -> None:
        print(f"OdsTabularWriter.write_rows: {len(rows)} rows")
        
        if not os.path.exists(self._filep):
            raise FileNotFoundError(f"Le fichier {self._filep} n'existe pas. Appelez write_header d'abord.")
        
        doc = opendocument.load(self._filep)
        
        tables = doc.spreadsheet.getElementsByType(Table)
        if not tables:
            raise ValueError("Aucune table trouvée dans le document")
        table = tables[0]
        
        for row_data in rows:
            row = TableRow()
            for cell_value in row_data:
                cell = TableCell()
                cell.addElement(P(text=str(cell_value)))
                row.addElement(cell)
            table.addElement(row)
        
        doc.save(self._filep)

    def close(self) -> None:
        print("OdsTabularWriter.close")