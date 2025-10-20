"""Module qui gère le système de publication/abonnement pour les événements Redis."""

import logging
from typing import Awaitable, Callable, Dict

from apis.clients import RedisClientHolder

logger = logging.getLogger(__name__)

EventHandler = Callable[[dict], Awaitable[None]]
event_handlers: Dict[str, EventHandler] = {}


def on_channel(channel: str):
    """Décorateur pour enregistrer une fonction comme gestionnaire d'événements pour un canal Redis spécifique."""
    if channel in event_handlers:
        raise ValueError("Un seul handler par canal est autorisé.")

    def decorator(func: EventHandler) -> EventHandler:
        event_handlers[channel] = func
        return func

    return decorator


async def listens(channels: list[str]):
    """Écoute des événements Redis."""

    rch = RedisClientHolder.get_application_instance()
    pubsub = rch.client.pubsub()
    await pubsub.psubscribe(*channels)
    logger.info(f"Abonné aux canaux {channels}")

    try:
        async for message in pubsub.listen():
            channel = message["channel"].decode() if isinstance(message["channel"], bytes) else message["channel"]

            if channel in event_handlers:
                handler = event_handlers[channel]
                try:
                    await handler(message)
                except Exception as e:
                    logger.error(f"Erreur lors du traitement du message sur le canal {channel}", exc_info=e)
    finally:
        await pubsub.unsubscribe(*channels)
        await pubsub.close()
