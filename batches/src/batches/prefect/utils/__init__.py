from prefect.client.orchestration import get_client
from prefect.exceptions import ObjectAlreadyExists
from prefect.client.schemas.actions import GlobalConcurrencyLimitCreate

import logging
from logging import Logger


async def ensure_concurrency_limit(name: str, limit: int = 1, logger: Logger = None):
    if logger is None:
        logger = logging.getLogger(__name__)

    async with get_client() as client:
        try:
            await client.create_global_concurrency_limit(GlobalConcurrencyLimitCreate(name=name, limit=limit))
        except ObjectAlreadyExists:
            logger.info(f"Global concurrency limit {name} already exists.")
