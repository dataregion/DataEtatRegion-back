from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # URLs de synchronisation
    url_init_sync_db: str = "http://localhost:5000/budget/api/v1/sync-referentiels"
    url_sync_db: str = "http://localhost:5000/budget/api/v1/sync-referentiels"
    token_sync_db: str = "GgqZ7LhmBOPsfJo9zH2aRTtJlzy9PV5G"

    # Mode développement
    dev_mode: bool = True
