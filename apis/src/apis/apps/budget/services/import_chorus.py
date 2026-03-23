import logging
import os
import csv
from uuid import uuid4
from models.exceptions import BadRequestError, ServerError
from apis.config.current import get_config
from apis.database import get_sesion_maker
from models.value_objects.UploadType import UploadType
from sqlalchemy.orm import Session
from models.connected_user import ConnectedUser
from services.audits.import_chorus_task import ImportChorusTaskService
from services.audits.upload_session import InitializeSessionRequest, MandatorySessionStateData, UploadSessionService


logger = logging.getLogger(__name__)


def validate_csv_file_content(file_path: str) -> None:
    """
    Valide que le fichier est vraiment un CSV et non un autre type de fichier.

    Cette fonction vérifie :
    1. Que le fichier peut être décodé en UTF-8 (détecte les fichiers binaires)
    2. Que le fichier peut être lu comme un CSV valide avec le sniffer

    Args:
        file_path: Chemin vers le fichier à valider

    Raises:
        BadRequestError: Si le fichier n'est pas un CSV valide
    """
    try:
        # Lire le fichier en UTF-8 strict (les fichiers binaires vont échouer ici)
        with open(file_path, "r", encoding="utf-8") as f:
            # Lire les 10 premières lignes pour valider la structure CSV
            sample_lines = [line for i, line in enumerate(f) if i < 10]

            if not sample_lines:
                raise BadRequestError(api_message="Le fichier CSV est vide")

            # Essayer de parser avec le module csv
            sample = "".join(sample_lines)
            try:
                # Détecter le dialecte CSV
                sniffer = csv.Sniffer()
                dialect = sniffer.sniff(sample, delimiters=",;\t")

                # Essayer de parser les lignes
                reader = csv.reader(sample_lines, dialect=dialect)
                rows = list(reader)

                if not rows:
                    raise BadRequestError(api_message="Le fichier CSV ne contient aucune donnée valide")

                # Vérifier qu'il y a au moins une colonne
                if rows and len(rows[0]) == 0:
                    raise BadRequestError(api_message="Le fichier CSV ne contient aucune colonne")

                logger.info(
                    f"Fichier CSV validé : {len(rows)} lignes lues, {len(rows[0]) if rows else 0} colonnes détectées"
                )

            except csv.Error as e:
                logger.error(f"Erreur lors de la lecture du fichier CSV : {e}", exc_info=e)
                raise BadRequestError(api_message="Le fichier ne peut pas être lu comme un CSV valide")

    except BadRequestError:
        # Relancer les BadRequestError sans les wrapper
        raise
    except UnicodeDecodeError:
        raise BadRequestError(api_message="Le fichier n'est pas un CSV")
    except Exception as e:
        logger.error(f"Erreur lors de la validation du fichier CSV : {e}", exc_info=e)
        raise BadRequestError(api_message=f"Erreur lors de la validation du fichier : {str(e)}")


def _get_upload_session_service() -> UploadSessionService:
    """Retourne une instance du service de gestion des sessions d'upload"""
    config = get_config()
    sessions_folder = os.path.join(config.upload.tus_folder, "sessions")
    return UploadSessionService(
        sessions_folder=sessions_folder,
        final_folder=config.upload.final_folder,
        db_session_factory=get_sesion_maker("main"),
    )


def initialize_upload_session(
    initialize_request: InitializeSessionRequest,
    user: ConnectedUser,
) -> str:
    """Initialise et persiste une session d'upload avant la réception des fichiers."""
    if initialize_request.total_ae_files < 1 or initialize_request.total_cp_files < 1:
        raise BadRequestError(api_message="total_ae_files and total_cp_files must be at least 1")

    session_token = str(uuid4())
    region = "NATIONAL" if user.current_region is None or user.current_region == "NAT" else user.current_region

    session_service = _get_upload_session_service()
    with session_service.borrow_session(session_token) as upload_session:
        try:
            upload_session.initialize(
                MandatorySessionStateData(
                    session_token=session_token,
                    total_ae_files=initialize_request.total_ae_files,
                    total_cp_files=initialize_request.total_cp_files,
                    year=initialize_request.year,
                    source_region=region,
                    username=user.email,
                ),
                client_id=user.azp or None,
            )
        except ValueError as e:
            logger.error(f"Failed to initialize upload session {session_token}: {e}", exc_info=e)
            raise BadRequestError(api_message=str(e))
        except Exception as e:
            logger.error(f"Failed to initialize upload session {session_token}: {e}", exc_info=e)
            raise ServerError(api_message=f"Failed to initialize upload session: {e}")

    return session_token


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

    # Vérifier la présence obligatoire de l'indice du fichier
    indice = metadata.get("indice")
    if indice is None:
        raise BadRequestError(api_message="indice is required")
    try:
        int(indice)
    except (ValueError, TypeError):
        raise BadRequestError(api_message="indice must be an integer")

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

    # Valider le contenu du fichier (vérifier que c'est bien un CSV)
    logger.info(f"Validating CSV file content: {file_path}")
    validate_csv_file_content(file_path)

    # Valider le contenu du fichier (vérifier que c'est bien un CSV)
    logger.info(f"Validating CSV file content: {file_path}")
    validate_csv_file_content(file_path)

    # Extraire les informations des metadata
    session_token = metadata.get("session_token")
    upload_type = metadata.get("uploadType")
    indice = int(metadata.get("indice"))

    # Enregistrer le fichier dans la session d'upload
    session_service = _get_upload_session_service()
    with session_service.borrow_session(session_token) as upload_session:
        try:
            session_state = upload_session.register_file(
                file_path=file_path,
                upload_type=upload_type,
                indice=indice,
            )
        except ValueError as e:
            logger.error(f"Failed to register file in session: {e}", exc_info=e)
            raise BadRequestError(api_message=str(e))
        except Exception as e:
            logger.error(f"Failed to register file in session: {e}", exc_info=e)
            raise ServerError(api_message=f"Failed to register file in session: {e}")

        # Vérifier si la session est complète
        if session_state.is_complete:
            logger.info(f"Session {session_token} is complete, finalizing...")

            try:
                # Concaténer les fichiers
                ae_final_path, cp_final_path = upload_session.finalize()

                # Insérer dans la table d'audit
                ImportChorusTaskService.process_upload_audit_final(
                    db=db,
                    email=user.email,
                    ae_path=ae_final_path,
                    cp_path=cp_final_path,
                    session_token=session_token,
                    year=session_state.year,
                    source_region=session_state.source_region,
                    client_id=user.azp or None,
                )

                logger.info(f"Session {session_token} finalized successfully")

            except Exception as e:
                logger.error(f"Failed to finalize session: {e}")
                raise ServerError(api_message=f"Failed to finalize session: {e}")
        else:
            logger.info(
                f"Session {session_token}: waiting for more files "
                f"({session_state.total_received}/{session_state.total_expected})"
            )
