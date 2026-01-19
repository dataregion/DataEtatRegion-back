import logging
import os
import shutil
from models.exceptions import BadRequestError, ServerError
from apis.config.current import get_config
from apis.apps.budget.models.upload import UploadType
from sqlalchemy.orm import Session
from models.connected_user import ConnectedUser
from services.audits.import_chorus_task import ImportChorusTaskService


logger = logging.getLogger(__name__)


def validate_metadata(metadata: dict):
    """Valide les metadata obligatoires et logue les informations"""
    logger.info(f"Validating metadata: {metadata}")

    # Vérifier la présence obligatoire du filename
    if "filename" not in metadata:
        raise BadRequestError(status_code=400, api_message="Filename is required")

    # Vérifier la présence obligatoire du token de session
    session_token = metadata.get("session_token")
    if session_token:
        logger.info(f"Session token found: {session_token}")
    else:
        raise BadRequestError(status_code=400, api_message="Session token is required")

    # Vérifier la présence obligatoire du uploadType
    upload_type = metadata.get("uploadType")
    if upload_type:
        # Valider que le uploadType est dans les valeurs autorisées
        valid_upload_types = [upload_type_enum.value for upload_type_enum in UploadType]
        if upload_type not in valid_upload_types:
            raise BadRequestError(
                status_code=400,
                api_message=f"Upload type {upload_type} not allowed. Valid types: {valid_upload_types}",
            )
        logger.info(f"Upload type found: {upload_type}")
    else:
        raise BadRequestError(status_code=400, api_message="Upload type is required")

    # Vérifier la présence obligatoire du filetype
    if "filetype" in metadata:
        logger.info(f"File type found: {metadata['filetype']}")
        allowed_types = [
            "text/csv",
        ]
        if metadata["filetype"] not in allowed_types:
            raise BadRequestError(
                status_code=400,
                api_message=f"File type {metadata['filetype']} not allowed",
            )
    else:
        raise BadRequestError(status_code=400, api_message="File type is required")

    logger.debug("Metadata validation passed")


def upload_complete(db: Session, user: ConnectedUser, file_path: str, metadata: dict):
    logger.info("Upload complete")

    # Valider les metadata
    validate_metadata(metadata)

    # Copy file to original filename from metadata if present
    filename = metadata.get("filename")
    new_path = None
    if filename:
        logger.info(f"Upload complete for file {filename} at {file_path}")
        dir_path = get_config().upload.final_folder
        new_path = os.path.join(dir_path, filename)
        try:
            shutil.move(file_path, new_path)
            logger.info(f"File moved to {new_path}")
        except Exception as e:
            logger.error(f"Failed to move file: {e}")
            raise ServerError(api_message=f"Failed to move file: {e}")
    else:
        logger.warning("No filename in metadata; file not moved")
        return

    # Traitement de l'audit via le service dédié
    ImportChorusTaskService.process_upload_audit(
        db=db,
        email=user.email,
        new_path=new_path,
        session_token=metadata.get("session_token"),
        upload_type=metadata.get("uploadType"),
        year=int(metadata.get("year")),
        source_region=user.current_region or "NATIONAL",
        client_id=user.azp or None,
    )
