import sys
from contextlib import asynccontextmanager

from fastapi.concurrency import run_in_threadpool


@asynccontextmanager
async def async_wrap_sync_cm(cm):
    """
    Appelle cm.__enter__ et cm.__exit__ dans un thread,
    yield la ressource dans le contexte async et transmet exc_info à __exit__.
    """
    exc_info = (None, None, None)
    resource = await run_in_threadpool(cm.__enter__)
    try:
        yield resource
    except Exception:
        exc_info = sys.exc_info()
        raise
    finally:
        await run_in_threadpool(cm.__exit__, *exc_info)
