from pathlib import Path
from setuptools import setup

self_path: Path = Path(__file__).parent

models_path: str = (self_path / ".." / "models").as_uri()
services_path: str = (self_path / ".." / "services").as_uri()
gristcli_path: str = (self_path / ".." / "gristcli").as_uri()


def read_requirements(filename):
    with open(filename) as f:
        return f.read().splitlines()

requirements = read_requirements("requirements.external.in")
requirements+= [
    f"models @ {models_path}",
    f"services @ {services_path}",
    f"gristcli @ {gristcli_path}",
]

setup(install_requires=requirements)
