"""
Package de services applicatifs.

Appelés par la couche web (les controleurs) et peut lancer des tâches asynchrones.
"""

from app.services import FileStorageProtocol


from werkzeug.datastructures import FileStorage


from os import PathLike


class WerkzeugFileStorage(FileStorageProtocol):
    """
    Proxy pour le filestorage de werkzeug
    """

    def __init__(self, proxied: FileStorage):
        self._proxied = proxied

    @classmethod
    def from_werkzeug_filestorage(cls, fs: FileStorage):
        return cls(fs)

    @property
    def filename(self):
        return self._proxied.filename

    def save(self, save_path: PathLike):
        self._proxied.save(save_path)
