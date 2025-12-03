import sys
import os
from pathlib import Path
from setuptools import setup

#
# XXX Dans le mécanisme de build.
# On n'inclut pas les sous modules lorsu'on est en mode transitif.
#
IS_TRANSITIVE_DEPENDENCY = bool(int(os.getenv("SERVICES_IS_TRANSITIVE_DEP", 1)))

self_path: Path = Path(__file__).parent

models_path: str = (self_path / ".." / "models").as_uri()


def read_requirements(filename):
    with open(filename) as f:
        return f.read().splitlines()


requirements = read_requirements("requirements.external.in")
if not IS_TRANSITIVE_DEPENDENCY:
    requirements += [
        f"models @ {models_path}",
    ]
else:
    print(
        ("services est traité comme une dépendance transitive. Les sous modules sont exclus du système de dépendance."),
        file=sys.stderr,
    )

setup(install_requires=requirements)
