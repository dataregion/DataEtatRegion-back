import logging
from typing import Dict, Any
import httpx
from fastapi import HTTPException, status, UploadFile

logger = logging.getLogger(__name__)


class SupersetAPIService:
    """Service pour gérer les appels à l'API Superset"""

    def __init__(self, base_url: str, api_key: str, timeout: float = 60.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    def _get_headers(self, token: str) -> Dict[str, str]:
        """Génère les headers communs pour les requêtes"""
        return {
            "X-API-Key": self.api_key,
            "Authorization": f"Bearer {token}",
        }

    async def check_user_exists(self, token: str) -> bool:
        """
        Vérifie si l'utilisateur existe dans Superset

        Args:
            token: Token d'authentification de l'utilisateur

        Returns:
            bool: True si l'utilisateur existe, False sinon

        Raises:
            HTTPException: En cas d'erreur de communication avec l'API
        """
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(f"Vérification de l'utilisateur via {self.base_url}/user/check")

            response = await client.get(
                f"{self.base_url}/user/check",
                headers=self._get_headers(token),
            )

            if response.status_code == 200:
                user_exists = response.json().get("exists", False)
                logger.info(f"Utilisateur {'trouvé' if user_exists else 'non trouvé'}")
                return user_exists

            logger.error(f"Erreur lors de la vérification utilisateur: {response.status_code}")
            return False

    async def import_table(
        self,
        token: str,
        file: UploadFile,
        table_id: str,
        columns_json: str,
    ) -> Dict[str, Any]:
        """
        Importe une table CSV dans Superset

        Args:
            token: Token d'authentification de l'utilisateur
            file: Fichier CSV à importer
            table_id: Identifiant de la table
            columns: Liste des colonnes validées (objet Pydantic)
            columns_json: JSON brut des colonnes à transmettre

        Returns:
            Dict contenant les résultats de l'import (rows_imported, message, etc.)

        Raises:
            HTTPException: En cas d'erreur lors de l'import
        """
        file_content = await file.read()

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(f"Envoi de la table '{table_id}' vers {self.base_url}/import/table")

            response = await client.post(
                f"{self.base_url}/import/table",
                files={
                    "file": (
                        file.filename or f"{table_id}.csv",
                        file_content,
                        "text/csv",
                    )
                },
                data={
                    "table_id": table_id,
                    "columns": columns_json,
                },
                headers=self._get_headers(token),
            )

            # Gestion des différents codes d'erreur
            if response.status_code == 403:
                logger.error("Erreur d'authentification avec l'API d'import")
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Erreur d'authentification avec l'API de destination",
                )
            if response.status_code == 400:
                error_data = response.json()
                logger.error(f"Erreur de validation côté API: {error_data}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_data.get("detail", "Erreur de validation des données"),
                )

            if response.status_code != 200:
                try:
                    error_detail = response.json().get("detail", response.text)
                except Exception:
                    error_detail = response.text

                logger.error(f"Erreur API ({response.status_code}): {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Erreur lors de l'import: {error_detail}",
                )

            # Succès
            result = response.json()
            logger.info(f"Import réussi: {result.get('rows_imported', 0)} lignes importées")

            return result

    async def link_to_superset(self, token: str, table_id: str):
        """
        Construit le liens avec Superset

        Args:
            token: Token d'authentification de l'utilisateur
            table_id: Identifiant de la table

        Returns:
            D

        Raises:
            HTTPException: En cas d'erreur lors du liens
        """

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(f"Envoi de la table '{table_id}' vers {self.base_url}/link-superset")

            response = await client.post(
                f"{self.base_url}/link-superset",
                data={
                    "table_id": table_id,
                },
                headers=self._get_headers(token),
            )

            response.raise_for_status()
            if response.status_code != 200:
                try:
                    error_detail = response.json().get("detail", response.text)
                except Exception:
                    error_detail = response.text

                logger.error(f"Erreur API Superset ({response.status_code}): {error_detail}")
                raise HTTPException(
                    status_code=response.status_code,
                    detail=f"Erreur lors du liens avec Superset: {error_detail}",
                )
            # Succès
            result = response.json()
            logger.info(f"Liens avec Superset pour{table_id} OK ")
            return result


def get_superset_service(base_url: str, api_key: str) -> SupersetAPIService:
    """Factory function pour créer une instance du service"""
    return SupersetAPIService(base_url, api_key)
