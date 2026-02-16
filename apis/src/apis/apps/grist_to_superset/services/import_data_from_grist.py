"""
Service pour gérer l'import de données CSV vers la base de données.
"""

import logging
from typing import List
import pandas as pd
from sqlalchemy import exc
from sqlalchemy import text
from sqlalchemy.orm import Session


from models.value_objects.to_superset import ColumnIn, ColumnType

from apis.apps.grist_to_superset.exceptions.import_data_exceptions import DataInsertException, DataInsertIndexException

logger = logging.getLogger(__name__)


class ImportService:
    """Service pour gérer l'import de données depuis Grist vers la base de données."""

    def __init__(self, session: Session):
        """
        Initialise le service d'import.

        Args:
            session: Session SQLAlchemy
        """
        self.session = session

    def import_table(
        self, table_id: str, dataframe: pd.DataFrame, columns_schema: List[ColumnIn], schema_name: str
    ) -> int:
        """
        Importe les données d'un DataFrame dans la base de données.

        Cette méthode orchestre tout le processus d'import :
        1. Création du schéma si nécessaire
        2. Création de la table
        3. Insertion des données

        Args:
            table_id: Identifiant de la table cible
            dataframe: DataFrame pandas contenant les données à importer
            columns_schema: Liste des colonnes avec leurs types

        Returns:
            int: Nombre de lignes importées

        Raises:
            DatabaseError: En cas d'erreur lors de l'import
        """
        logger.info(f"Début de l'import pour la table '{table_id}'")

        # 1. Créer le schéma s'il n'existe pas
        self._create_schema_if_not_exists(schema_name)

        if self.table_exists(schema_name=schema_name, table_name=table_id):
            logger.info(f"La table '{schema_name}.{table_id}' existe déjà. Suppression avant réimport.")
            self.delete_table(schema_name=schema_name, table_name=table_id)

        # 2. Créer la table
        self._create_table_if_not_exists(schema_name=schema_name, table_name=table_id, columns_schema=columns_schema)
        logger.debug("Commit après création du schéma et de la table")

        # 3. Insérer les données
        rows_imported = self._insert_data(
            schema_name=schema_name, table_name=table_id, dataframe=dataframe, columns_schema=columns_schema
        )

        logger.info(f"Import terminé: {rows_imported} lignes importées dans '{table_id}'")
        return rows_imported

    def _create_schema_if_not_exists(self, schema_name: str) -> None:
        """
        Crée un schéma dans la base de données s'il n'existe pas.

        Args:
            schema_name: Nom du schéma à créer

        Example:
            await service._create_schema_if_not_exists(schema_name)
        """
        query = text(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
        self.session.execute(query)
        logger.info(f"Schéma '{schema_name}' vérifié/créé")

    def _create_table_if_not_exists(self, schema_name: str, table_name: str, columns_schema: List[ColumnIn]) -> None:
        """
        Crée une table dans la base de données si elle n'existe pas.

        Args:
            schema_name: Nom du schéma contenant la table
            table_name: Nom de la table à créer
            columns_schema: Liste des colonnes avec leurs types

        Example:
            columns = [
                ColumnIn(id="name", type="text", is_index=True),
                ColumnIn(id="age", type="numeric", is_index=False)
            ]
            await service._create_table_if_not_exists("grist_data", "users", columns)
        """
        # Construire les définitions de colonnes
        column_definitions = []
        primary_keys = []

        for col in columns_schema:
            sql_type = self._map_column_type_to_sql(col.type)
            column_def = f'"{col.id}" {sql_type}'

            if col.is_index:
                primary_keys.append(f'"{col.id}"')

            column_definitions.append(column_def)

        # Ajouter la contrainte de clé primaire si nécessaire
        if primary_keys:
            column_definitions.append(f"PRIMARY KEY ({', '.join(primary_keys)})")

        # Créer la requête SQL
        columns_sql = ",\n    ".join(column_definitions)
        query = text(f"""
            CREATE TABLE IF NOT EXISTS {schema_name}."{table_name}" (
                {columns_sql}
            )
        """)

        self.session.execute(query)
        self.session.commit()
        logger.info(f"Table '{schema_name}.{table_name}' vérifiée/créée avec {len(columns_schema)} colonnes")

    def _insert_data(
        self, schema_name: str, table_name: str, dataframe: pd.DataFrame, columns_schema: List[ColumnIn]
    ) -> int:
        """
        Insère les données d'un DataFrame dans une table.

        Args:
            schema_name: Nom du schéma contenant la table
            table_name: Nom de la table cible
            dataframe: DataFrame contenant les données à insérer
            columns_schema: Liste des colonnes avec leurs types

        Returns:
            int: Nombre de lignes insérées

        Example:
            rows = await service._insert_data("grist_data", "users", df, columns)
        """
        if dataframe.empty:
            logger.warning("DataFrame vide, aucune donnée à insérer")
            return 0

        column_names = [col.id for col in columns_schema]
        df_to_insert = dataframe[column_names]

        try:
            df_to_insert.to_sql(
                name=table_name,
                con=self.session.get_bind(),
                schema=schema_name,
                if_exists="append",
                index=False,
                method="multi",
                chunksize=1000,
            )
            self.session.commit()
            logger.info(f"{len(df_to_insert)} lignes insérées dans '{schema_name}.{table_name}'")

            return len(df_to_insert)

        except exc.IntegrityError as i:
            self.session.rollback()
            logger.error(f"Erreur integrite : {str(i)}")
            index_col = next((col.id for col in columns_schema if col.is_index), None)
            if index_col:
                raise DataInsertIndexException(
                    f"L'index '{index_col}' ne contient pas des valeurs uniques. "
                    "Merci de sélectionner un index qui contient uniquement des valeurs uniques."
                ) from i
            else:
                raise DataInsertException(
                    "Erreur d'intégrité lors de l'insertion des données. "
                    "Il est recommandé de définir un index avec des valeurs uniques pour éviter les doublons."
                ) from i
        except Exception as e:
            self.session.rollback()
            logger.error(f"Erreur lors de l'insertion: {str(e)}")
            raise DataInsertException() from e

    def _map_column_type_to_sql(self, column_type: ColumnType) -> str:
        """
        Convertit un type de colonne en type SQL PostgreSQL.

        Args:
            column_type: Type de la colonne (enum ColumnType)

        Returns:
            str: Type SQL correspondant

        Example:
            sql_type = service._map_column_type_to_sql(ColumnType.TEXT)
            # Retourne: "TEXT"
        """
        type_mapping = {
            ColumnType.TEXT: "TEXT",
            ColumnType.NUMERIC: "NUMERIC",
            ColumnType.INT: "NUMERIC",
            ColumnType.DATE: "DATE",
            ColumnType.DATETIME: "TIMESTAMP",
            ColumnType.BOOL: "BOOLEAN",
        }

        return type_mapping.get(column_type, "TEXT")

    def table_exists(self, schema_name: str, table_name: str) -> bool:
        """
        Vérifie si une table existe dans la base de données.

        Args:
            schema_name: Nom du schéma
            table_name: Nom de la table

        Returns:
            bool: True si la table existe, False sinon
        """
        query = text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = :schema_name
                AND table_name = :table_name
            )
        """)

        result = self.session.execute(query, {"schema_name": schema_name, "table_name": table_name})
        exists = result.scalar()

        return bool(exists)

    def delete_table(self, schema_name: str, table_name: str) -> None:
        """
        Supprime une table de la base de données.

        Args:
            schema_name: Nom du schéma
            table_name: Nom de la table à supprimer

        Warning:
            Cette opération est irréversible !
        """
        query = text(f'DROP TABLE IF EXISTS {schema_name}."{table_name}" CASCADE')
        self.session.execute(query)
        self.session.commit()
        logger.info(f"Table '{schema_name}.\"{table_name}\"' supprimée")
