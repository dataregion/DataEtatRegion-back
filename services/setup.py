from pathlib import Path
from setuptools import setup

self_path: Path = Path(__file__).parent

models_path: str = (self_path / ".." / "models").as_uri()


def read_requirements(filename):
    with open(filename) as f:
        return f.read().splitlines()


setup(
    install_requires=[
        # Dépendances locales
        f"models @ {models_path}",
    ]
)
