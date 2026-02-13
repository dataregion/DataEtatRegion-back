from sqlalchemy.orm import Session
from models.entities.audit.AuditInsertFinancialTasks import AuditInsertFinancialTasks
from models.value_objects.UploadType import UploadType
from models.exceptions import ServerError
import logging

logger = logging.getLogger(__name__)


class ImportChorusTaskService:
    @staticmethod
    def process_upload_audit(
        db: Session,
        email: str,
        new_path: str,
        session_token: str,
        upload_type: UploadType,
        year: int,
        source_region: str,
        client_id: str = None,
    ) -> None:
        """
        Traite l'insertion ou la mise à jour de l'audit pour les uploads de fichiers financiers

        Args:
            db: Session de base de données audit
            email: Adresse email de l'utilisateur connecté
            new_path: Chemin du fichier uploadé
            session_token: Token de session unique
            upload_type: Type d'upload (financial-ae ou financial-cp)
            year: Année des données
        """
        if not session_token or not upload_type or not year:
            logger.error("Missing required metadata for audit tracking")
            return

        try:
            # Chercher une entrée existante avec le même session_token
            existing_record = (
                db.query(AuditInsertFinancialTasks)
                .filter_by(
                    session_token=session_token,
                    username=email,
                    source_region=source_region,
                )
                .first()
            )

            if existing_record:
                # Mettre à jour la ligne existante
                logger.info(f"Updating existing record for session_token: {session_token}")
                if upload_type == UploadType.FINANCIAL_AE.value:
                    existing_record.fichier_ae = new_path
                elif upload_type == UploadType.FINANCIAL_CP.value:
                    existing_record.fichier_cp = new_path
                logger.info(f"Updated record with {upload_type} file: {new_path}")
            else:
                # Créer une nouvelle ligne
                logger.info(f"Creating new record for session_token: {session_token}")

                # Déterminer les fichiers selon le type d'upload
                fichier_ae = new_path if upload_type == UploadType.FINANCIAL_AE.value else None
                fichier_cp = new_path if upload_type == UploadType.FINANCIAL_CP.value else None

                new_record = AuditInsertFinancialTasks(
                    session_token=session_token,
                    fichier_ae=fichier_ae,
                    fichier_cp=fichier_cp,
                    source_region=source_region,
                    annee=year,
                    username=email,
                    application_clientid=client_id,
                )
                db.add(new_record)
                logger.info(f"Created new record with {upload_type} file: {new_path}")

            # Commit les changements
            db.commit()
            logger.info(f"Successfully processed upload for session_token: {session_token}")

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to update audit table: {e}")
            raise ServerError(api_message=f"Failed to update audit table: {e}")

    @staticmethod
    def process_upload_audit_final(
        db: Session,
        email: str,
        ae_path: str,
        cp_path: str,
        session_token: str,
        year: int,
        source_region: str,
        client_id: str = None,
    ) -> None:
        """
        Insère l'audit final après concaténation des fichiers AE et CP.

        Cette méthode est appelée quand tous les fichiers d'une session d'upload
        ont été reçus et concaténés.

        Args:
            db: Session de base de données audit
            email: Adresse email de l'utilisateur connecté
            ae_path: Chemin du fichier AE concaténé
            cp_path: Chemin du fichier CP concaténé
            session_token: Token de session unique
            year: Année des données
            source_region: Région source
            client_id: ID client de l'application (optionnel)
        """
        if not session_token or not year:
            logger.error("Missing required metadata for audit tracking")
            return

        try:
            # Créer une nouvelle entrée avec les deux fichiers concaténés
            logger.info(f"Creating final audit record for session_token: {session_token}")

            new_record = AuditInsertFinancialTasks(
                session_token=session_token,
                fichier_ae=ae_path,
                fichier_cp=cp_path,
                source_region=source_region,
                annee=year,
                username=email,
                application_clientid=client_id,
            )
            db.add(new_record)

            # Commit les changements
            db.commit()
            logger.info(
                f"Successfully created final audit record for session_token: {session_token}, "
                f"AE: {ae_path}, CP: {cp_path}"
            )

        except Exception as e:
            db.rollback()
            logger.error(f"Failed to create final audit record: {e}")
            raise ServerError(api_message=f"Failed to create final audit record: {e}")
