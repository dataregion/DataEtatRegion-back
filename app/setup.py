from pathlib import Path
from setuptools import setup

self_path: str = (Path(__file__).parent).as_uri()


def read_requirements(filename):
    with open(filename) as f:
        return f.read().splitlines()


setup(
    install_requires=[
        read_requirements("requirements.external.in"),
        # Dépendances locales
        # f"persistence @ {persistence_path}",
    ]
)
