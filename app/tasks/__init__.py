import logging
import pika
import time
from functools import wraps
from tenacity import retry, stop_after_attempt

from app import celeryapp

logger = logging.getLogger()
celery = celeryapp.celery
from celery import current_app

__all__ = (
    "limiter_queue",
    "LimitQueueException",
)


MAX_QUEUE_SIZE = "max_queue_size"
TIMEOUT_QUEUE_RETRY = "timeout_queue_retry"
DEFAULT_MAX_QUEUE_SIZE = 100000
DEFAULT_TIMEOUT_QUEUE_RETRY = 60

max_queue_size = current_app.conf[MAX_QUEUE_SIZE] if MAX_QUEUE_SIZE in current_app.conf else DEFAULT_MAX_QUEUE_SIZE
timeout_queue_retry = (
    current_app.conf[TIMEOUT_QUEUE_RETRY] if TIMEOUT_QUEUE_RETRY in current_app.conf else DEFAULT_TIMEOUT_QUEUE_RETRY
)


def lazy_rabbit_connector():
    conn = None
    chan = None

    def get_connection():
        nonlocal conn
        nonlocal chan

        if current_app.conf.broker_url is None:
            return None

        if conn is None or conn.is_closed:
            conn = pika.BlockingConnection(pika.URLParameters(current_app.conf.broker_url))

        if chan is None or chan.is_closed:
            chan = conn.channel()

        return chan

    return get_connection


lazy_channel = lazy_rabbit_connector()


def limiter_queue(
    queue_name: str, max_queue_size: int = max_queue_size, timeout_queue_retry: int = timeout_queue_retry
):
    """
    Vérifie que le nombre de message dans la file "queue_name" de rabbitmq n'atteint pas la taille max
    Si taille max dépassé, attente de 10 seconde.
    :return:
    """

    def wrapper(func):
        @wraps(func)
        def inner_wrapper(*args, **kwargs):
            if not current_app.conf.task_always_eager:
                num_retries = 0

                while True:
                    queue_info = _get_queue(queue_name)
                    msg_count = queue_info.method.message_count

                    if msg_count <= max_queue_size:
                        break
                    if num_retries >= timeout_queue_retry:
                        raise LimitQueueException(
                            f"Timeout exceeded while waiting for the queue '{queue_name}' to be available."
                        )

                    logger.warning(f"Limite de la file rabbitmq atteinte. On attend 10 secondes")
                    time.sleep(10)
                    num_retries += 1

            return func(*args, **kwargs)

        return inner_wrapper

    return wrapper


class LimitQueueException(Exception):
    pass


@retry(stop=stop_after_attempt(2))
def _get_queue(queue_name: str):
    channel = lazy_channel()
    queue = channel.queue_declare(queue_name, passive=True) if channel is not None else None
    return queue


from .files.file_task import *
from .financial.import_financial import *
from .financial.import_france_2030 import *
from .financial.visuterritoire import *
from .import_refs_tasks import *
from .management_tasks import *
from .refs import *
from .siret import *
