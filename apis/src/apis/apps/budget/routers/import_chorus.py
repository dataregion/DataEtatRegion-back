import logging
from tuspyserver import create_tus_router
from apis.apps.budget.services.import_chorus import pre_create_hook, on_upload_complete
from apis.config.current import get_config

logger = logging.getLogger(__name__)
config = get_config()


tus_router = create_tus_router(
    files_dir=str(config.upload.tus_folder),
    max_size=config.upload.max_size,
    pre_create_hook=pre_create_hook,
    on_upload_complete=on_upload_complete,
    prefix="import",
    tags=["Import Chorus"],
)
