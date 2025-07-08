from setuptools import setup


def read_requirements(filename):
    with open(filename) as f:
        return f.read().splitlines()


setup(
    install_requires=[
        read_requirements("requirements.external.in"),
    ]
)
