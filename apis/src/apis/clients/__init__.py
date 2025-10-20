import logging
import redis.asyncio as redis
from apis.config.current import get_config

logger = logging.getLogger(__name__)

_instance = None


class RedisClientHolder:
    def __init__(self, redis_client: redis.Redis):
        self.logger = logging.getLogger(f"{__name__}.{self.__class__.__name__}")
        self.client = redis_client

    async def close(self):
        self.logger.info("Fermeture de la connexion au redis applicatif")
        await self.client.close()

    @staticmethod
    def get_application_instance():
        global _instance
        if _instance is None:
            config = get_config()
            redis_conf = config.redis_applicatif

            logger.info(
                "Connexion au redis applicatif sur redis://%s:%s/%s", redis_conf.host, redis_conf.port, redis_conf.db
            )
            redis_cli = redis.from_url(f"redis://{redis_conf.host}", port=redis_conf.port, db=redis_conf.db)
            _instance = RedisClientHolder(redis_cli)
        return _instance
