"""Module de conversion de fichiers CSV vers d'autres formats (Excel, ODS).

Ce module permet de convertir des fichiers CSV volumineux vers Excel ou ODS
en lecture streaming pour minimiser la consommation mémoire.
"""

import csv
from pathlib import Path
from openpyxl import Workbook
from odf import opendocument
from odf.table import Table, TableRow, TableCell
from odf.text import P


def convert_csv_to_excel(csv_path: Path, target_path: Path, chunk_size: int = 1000) -> None:
    """Convertit un fichier CSV en Excel (.xlsx) en streaming.

    Args:
        csv_path: Chemin du fichier CSV source
        target_path: Chemin du fichier Excel cible
        chunk_size: Nombre de lignes à traiter par batch (défaut: 1000)

    Raises:
        FileNotFoundError: Si le fichier CSV n'existe pas
        ValueError: Si le fichier CSV est vide
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Le fichier CSV {csv_path} n'existe pas")

    print(f"Conversion CSV → Excel: {csv_path} → {target_path}")

    wb = Workbook()
    ws = wb.active

    total_rows = 0

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)

        # Traiter les lignes par chunks pour minimiser l'usage mémoire
        chunk = []
        for row in reader:
            chunk.append(row)
            total_rows += 1

            if len(chunk) >= chunk_size:
                for row_data in chunk:
                    ws.append(row_data)
                chunk = []
                print(f"  → {total_rows} lignes converties...")

        # Traiter les lignes restantes
        if chunk:
            for row_data in chunk:
                ws.append(row_data)
            print(f"  → {total_rows} lignes converties...")

    if total_rows == 0:
        raise ValueError(f"Le fichier CSV {csv_path} est vide")

    wb.save(str(target_path))
    print(f"✓ Conversion terminée: {total_rows} lignes écrites dans {target_path}")


def convert_csv_to_ods(csv_path: Path, target_path: Path, chunk_size: int = 1000) -> None:
    """Convertit un fichier CSV en ODS en streaming.

    Args:
        csv_path: Chemin du fichier CSV source
        target_path: Chemin du fichier ODS cible
        chunk_size: Nombre de lignes à traiter par batch (défaut: 1000)

    Raises:
        FileNotFoundError: Si le fichier CSV n'existe pas
        ValueError: Si le fichier CSV est vide
    """
    if not csv_path.exists():
        raise FileNotFoundError(f"Le fichier CSV {csv_path} n'existe pas")

    print(f"Conversion CSV → ODS: {csv_path} → {target_path}")

    doc = opendocument.OpenDocumentSpreadsheet()
    table = Table(name="Sheet1")

    total_rows = 0

    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)

        # Traiter les lignes par chunks pour minimiser l'usage mémoire
        for i, row_data in enumerate(reader):
            row = TableRow()
            for cell_value in row_data:
                cell = TableCell()
                cell.addElement(P(text=str(cell_value)))
                row.addElement(cell)
            table.addElement(row)
            total_rows += 1

            # Afficher la progression tous les chunk_size lignes
            if (i + 1) % chunk_size == 0:
                print(f"  → {total_rows} lignes converties...")

    if total_rows == 0:
        raise ValueError(f"Le fichier CSV {csv_path} est vide")

    doc.spreadsheet.addElement(table)
    doc.save(str(target_path))
    print(f"✓ Conversion terminée: {total_rows} lignes écrites dans {target_path}")
