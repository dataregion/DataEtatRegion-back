from http import HTTPStatus
import logging
from fastapi import Depends
from tuspyserver import create_tus_router
from apis.apps.budget.services.import_chorus import validate_metadata, upload_complete
from apis.config.current import get_config
from apis.database import get_session_audit
from models.connected_user import ConnectedUser
from models.exceptions import BadRequestError

from apis.security.keycloak_token_validator import KeycloakTokenValidator


logger = logging.getLogger(__name__)
config = get_config()
keycloak_validator = KeycloakTokenValidator.get_application_instance()


def pre_create_hook(
    user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user_admin_or_comptable()),
):
    async def handler(metadata: dict, upload_info: dict):
        logger.info("Pre-Create Hook called")

        # Valider les metadata
        validate_metadata(metadata)

        # Example: Check file size limits (1GB)
        config = get_config()
        if upload_info["size"] and upload_info["size"] > config.upload.max_size:
            raise BadRequestError(
                code=HTTPStatus.REQUEST_ENTITY_TOO_LARGE,
                api_message=f"File too large (max {config.upload.max_size} bytes)",
            )

        logger.debug("Pre-Create Hook validation passed")

    return handler


def on_upload_complete(
    db=Depends(get_session_audit),
    current_user: ConnectedUser = Depends(keycloak_validator.afn_get_connected_user_admin_or_comptable()),
):
    def handler(file_path: str, metadata: dict):
        upload_complete(db=db, user=current_user, file_path=file_path, metadata=metadata)

    return handler


tus_router = create_tus_router(
    files_dir=str(config.upload.tus_folder),
    max_size=config.upload.max_size,
    auth=keycloak_validator.afn_get_connected_user_admin_or_comptable(),
    pre_create_dep=pre_create_hook,
    upload_complete_dep=on_upload_complete,
    prefix="import",
    tags=["Import Chorus"],
)
