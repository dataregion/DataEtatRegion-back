from abc import ABC
from enum import Enum
from io import StringIO
from typing import Iterable, List, Tuple

import pandas as pd
from pydantic import BaseModel, ConfigDict

from models.value_objects.colonne_csv import ColonneCsv


EMPTY_STRINGS = {
    "",
    "n/a",
    "na",
    "nr",
    "(vide)",
    "-",
    "--",
}


class SchemaCsv(BaseModel, ABC):
    """
    Schéma CSV minimal et robuste.

    Responsabilités :
    - définir les colonnes attendues
    - valider la structure (header)
    - valider / filtrer les lignes (required + type)
    - fournir une lecture chunkée standard
    """

    model_config = ConfigDict(arbitrary_types_allowed=True)

    colonnes: dict[Enum, ColonneCsv]
    # =======================================================
    # Métadonnées
    # =======================================================

    def expected_columns(self) -> List[str]:
        return [c.name for c in self.colonnes]

    def required_columns(self) -> set[str]:
        return {c.name for c in self.colonnes if c.required}

    def pandas_dtypes(self) -> dict:
        return {c.name: c.dtype for c in self.colonnes if c.dtype is not None}

    def is_effectively_empty(self, value) -> bool:
        if pd.isna(value):
            return True
        if isinstance(value, str):
            return value.strip().lower() in EMPTY_STRINGS
        return False

    # =======================================================
    # Validation structurelle (bloquante)
    # =======================================================

    def _read_header(self, file, *, sep: str = ";") -> list[str]:
        """
        Lit uniquement le header du CSV (aucune donnée).
        """
        df = pd.read_csv(file, sep=sep, nrows=0)
        return list(df.columns)

    def validate_header(self, file, *, sep: str = ";") -> None:
        """
        Valide :
        - colonnes requises
        - colonnes inattendues
        """
        errors = []

        expected = set(self.expected_columns())
        required = self.required_columns()
        provided = set(self._read_header(file, sep=sep))

        missing = required - provided
        extra = provided - expected

        if missing:
            errors.append(f"Colonnes manquantes : {sorted(missing)}")
        if extra:
            errors.append(f"Colonnes inattendues : {sorted(extra)}")

        if errors:
            raise ValueError(" | ".join(errors))

    # =======================================================
    # Validation ligne par ligne (tolérante)
    # =======================================================

    def cast_valid_rows(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Applique les dtype métier sur des lignes déjà validées.
        """
        df = df.copy()

        for col in self.colonnes:
            if col.dtype:
                df[col.name] = df[col.name].apply(lambda v: None if self.is_effectively_empty(v) else col.dtype(v))

        return df

    def validate_rows(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Valide chaque ligne :
        - champs requis
        - typage

        Retourne :
        - lignes valides
        - lignes invalides
        """
        valid_mask = pd.Series(True, index=df.index)

        for col in self.colonnes:
            series = df[col.name]

            # ---------- required ----------
            if col.required:
                present_mask = ~series.apply(self.is_effectively_empty)
                valid_mask &= present_mask

            # ---------- type ----------
            if col.dtype:

                def is_valid_type(value):
                    if self.is_effectively_empty(value):
                        return True
                    try:
                        col.dtype(value)
                        return True
                    except Exception:
                        return False

                type_mask = series.apply(is_valid_type)
                valid_mask &= type_mask

        return df[valid_mask], df[~valid_mask]

    # =======================================================
    # Lecture chunkée
    # =======================================================

    def read_chunks(
        self,
        file,
        *,
        sep: str = ";",
        chunksize: int = 100_000,
        **kwargs,
    ) -> Iterable[pd.DataFrame]:
        """
        Lecture streaming d'un CSV volumineux.
        """
        return pd.read_csv(
            file,
            sep=sep,
            chunksize=chunksize,
            dtype=str,
            keep_default_na=False,
            **kwargs,
        )

    # =======================================================
    # Génération CSV exemple
    # =======================================================

    def generate_example_csv(self, rows: int = 3) -> str:
        data = {col.name: ([col.example] * rows if col.example is not None else [None] * rows) for col in self.colonnes}

        df = pd.DataFrame(data)
        buf = StringIO()
        df.to_csv(buf, index=False)
        return buf.getvalue()
