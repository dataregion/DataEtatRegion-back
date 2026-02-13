import logging
import os
from models.exceptions import BadRequestError, ServerError
from apis.config.current import get_config
from models.value_objects.UploadType import UploadType
from sqlalchemy.orm import Session
from models.connected_user import ConnectedUser
from services.audits.import_chorus_task import ImportChorusTaskService
from services.audits.upload_session import UploadSessionService


logger = logging.getLogger(__name__)


def _get_upload_session_service() -> UploadSessionService:
    """Retourne une instance du service de gestion des sessions d'upload"""
    config = get_config()
    sessions_folder = os.path.join(config.upload.tus_folder, "sessions")
    return UploadSessionService(
        sessions_folder=sessions_folder,
        final_folder=config.upload.final_folder,
    )


def validate_metadata(metadata: dict):
    """Valide les metadata obligatoires et logue les informations"""
    logger.info(f"Validating metadata: {metadata}")

    # Vérifier la présence obligatoire du filename
    if "filename" not in metadata:
        raise BadRequestError(api_message="Filename is required")

    # Vérifier la présence obligatoire du token de session
    session_token = metadata.get("session_token")
    if session_token:
        logger.info(f"Session token found: {session_token}")
    else:
        raise BadRequestError(api_message="Session token is required")

    # Vérifier la présence obligatoire du uploadType
    upload_type = metadata.get("uploadType")
    if upload_type:
        # Valider que le uploadType est dans les valeurs autorisées
        valid_upload_types = [upload_type_enum.value for upload_type_enum in UploadType]
        if upload_type not in valid_upload_types:
            raise BadRequestError(
                api_message=f"Upload type {upload_type} not allowed. Valid types: {valid_upload_types}",
            )
        logger.info(f"Upload type found: {upload_type}")
    else:
        raise BadRequestError(api_message="Upload type is required")

    # Vérifier la présence obligatoire du filetype
    if "filetype" in metadata:
        logger.info(f"File type found: {metadata['filetype']}")
        allowed_types = [
            "text/csv",
        ]
        if metadata["filetype"] not in allowed_types:
            raise BadRequestError(
                api_message=f"File type {metadata['filetype']} not allowed",
            )
    else:
        raise BadRequestError(api_message="File type is required")

    # Vérifier la présence obligatoire de total_ae_files et total_cp_files
    total_ae_files = metadata.get("total_ae_files")
    total_cp_files = metadata.get("total_cp_files")

    if total_ae_files is None:
        raise BadRequestError(api_message="total_ae_files is required")
    if total_cp_files is None:
        raise BadRequestError(api_message="total_cp_files is required")

    try:
        total_ae = int(total_ae_files)
        total_cp = int(total_cp_files)
        if total_ae < 1 or total_cp < 1:
            raise BadRequestError(api_message="total_ae_files and total_cp_files must be at least 1")
        logger.info(f"Expected files: AE={total_ae}, CP={total_cp}")
    except ValueError:
        raise BadRequestError(api_message="total_ae_files and total_cp_files must be integers")

    logger.debug("Metadata validation passed")


def upload_complete(db: Session, user: ConnectedUser, file_path: str, metadata: dict):
    """Traite la fin d'un upload de fichier.

    Enregistre le fichier dans la session d'upload et, quand tous les fichiers
    de la session sont reçus, concatène les fichiers AE et CP puis insère
    le résultat dans la table AuditInsertFinancialTasks.
    """
    logger.info("Upload complete")

    # Valider les metadata
    validate_metadata(metadata)

    # Extraire les informations des metadata
    session_token = metadata.get("session_token")
    upload_type = metadata.get("uploadType")
    total_ae_files = int(metadata.get("total_ae_files"))
    total_cp_files = int(metadata.get("total_cp_files"))
    year = int(metadata.get("year"))

    region = "NATIONAL" if user.current_region is None or user.current_region == "NAT" else user.current_region

    # Enregistrer le fichier dans la session d'upload
    session_service = _get_upload_session_service()

    try:
        session_state = session_service.register_file(
            file_path=file_path,
            session_token=session_token,
            upload_type=upload_type,
            total_ae_files=total_ae_files,
            total_cp_files=total_cp_files,
            year=year,
            source_region=region,
            username=user.email,
            client_id=user.azp or None,
        )
    except Exception as e:
        logger.error(f"Failed to register file in session: {e}")
        raise ServerError(api_message=f"Failed to register file in session: {e}")

    # Vérifier si la session est complète
    if session_state.is_complete:
        logger.info(f"Session {session_token} is complete, finalizing...")

        try:
            # Concaténer les fichiers
            ae_final_path, cp_final_path = session_service.finalize_session(session_token)

            # Insérer dans la table d'audit
            ImportChorusTaskService.process_upload_audit_final(
                db=db,
                email=user.email,
                ae_path=ae_final_path,
                cp_path=cp_final_path,
                session_token=session_token,
                year=year,
                source_region=region,
                client_id=user.azp or None,
            )

            # Nettoyer les fichiers temporaires de la session
            session_service.cleanup_session(session_token)

            logger.info(f"Session {session_token} finalized successfully")

        except Exception as e:
            logger.error(f"Failed to finalize session: {e}")
            raise ServerError(api_message=f"Failed to finalize session: {e}")
    else:
        logger.info(
            f"Session {session_token}: waiting for more files "
            f"({session_state.total_received}/{session_state.total_expected})"
        )
