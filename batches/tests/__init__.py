import os
from pathlib import Path


TESTS_PATH = Path(os.path.dirname(__file__))

# On set ici l'URL du container Prefect, sinon Prefect va s'init avec le port 4200
os.environ["PREFECT_API_URL"] = "http://127.0.0.1:4281/api"
