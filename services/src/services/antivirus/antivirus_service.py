"""
Service de scan antivirus pour les fichiers uploadés.

Appelle le démon ClamAV (clamd) via TCP (INSTREAM).
Politique MVP budget national : fail closed — tout fichier dont le scan ne peut
pas être validé est rejeté.
"""

from collections.abc import Callable
from contextlib import contextmanager
import logging
import os
import tempfile
from typing import BinaryIO, ContextManager, Generator

import clamd
from services.antivirus.exceptions import AntivirusError, AntivirusScanError, VirusFoundError

logger = logging.getLogger(__name__)

CustomTimeoutFn = Callable[[int], int]
"""Fonction qui calcule un timeout (secondes) à partir d'une taille de fichier (bytes)"""

DEFAULT_STREAM_CHUNK_SIZE = 1024 * 1024
"""Taille par défaut (1 MiB) pour les copies de flux en mémoire bornée."""


def compute_antivirus_timeout(file_size: int, intitial_timeout: int, secon_per_gb: int, max_timeout: int) -> int:
    """Ajuste le timeout en fonction de la taille du fichier, borné par la configuration."""
    nb_gb = file_size / (1024 * 1024 * 1024)
    return min(max_timeout, intitial_timeout + (secon_per_gb * nb_gb))


def compute_default_av_timeout(file_size: int, max_timeout: int) -> int:
    """Exemple de fonction de timeout personnalisé : 30s de base + 10s par GB, max 5min."""
    return compute_antivirus_timeout(file_size, intitial_timeout=30, secon_per_gb=10, max_timeout=max_timeout)


class AntivirusService:
    """Interface vers le démon clamd pour le scan de fichiers uploadés."""

    def __init__(self, host: str, port: int, timeout: int = 60, max_file_size_bytes: int = 25 * 1024 * 1024) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._max_file_size_bytes = max_file_size_bytes

    def default_timeout_fn(self, file_size: int) -> int:
        """Fonction de timeout par défaut, basée sur la taille du fichier."""
        return compute_default_av_timeout(file_size, max_timeout=self._timeout)

    def scanned_binary_io(
        self,
        binary_io: BinaryIO,
        context: dict | None = None,
        custom_timeout_fn: CustomTimeoutFn | None = None,
    ) -> ContextManager[BinaryIO]:
        @contextmanager
        def _manager() -> Generator[BinaryIO, None, None]:
            with tempfile.NamedTemporaryFile(delete=True) as temp_file:
                while True:
                    chunk = binary_io.read(DEFAULT_STREAM_CHUNK_SIZE)
                    if not chunk:
                        break
                    temp_file.write(chunk)
                temp_file.flush()

                self.scan_file(
                    file_path=temp_file.name,
                    context=context,
                    custom_timeout_fn=custom_timeout_fn,
                )

                temp_file.seek(0)
                yield temp_file

        return _manager()

    def scan_file(
        self,
        file_path: str,
        context: dict | None = None,
        custom_timeout_fn: CustomTimeoutFn | None = None,
    ) -> None:
        """Scanne un fichier via ClamAV INSTREAM et lève une exception en cas de problème.

        Args:
            file_path: Chemin local vers le fichier à scanner.
            context: Contexte pour les logs (session_token, filename, uploadType, user…).
            custom_timeout_fn: Fonction optionnelle permettant de calculer le timeout
                à partir de la taille du fichier en octets.

        Raises:
            VirusFoundError: Le fichier contient un virus détecté.
            AntivirusScanError: Le service antivirus est indisponible, en timeout ou en erreur.
        """
        if custom_timeout_fn is None:
            custom_timeout_fn = self.default_timeout_fn

        ctx_str = " | ".join(f"{k}={v}" for k, v in (context or {}).items())

        try:
            file_size = os.path.getsize(file_path)
            if file_size > self._max_file_size_bytes:
                logger.warning(
                    "Fichier refusé: taille trop grande (%s > %s) [%s]",
                    file_size,
                    self._max_file_size_bytes,
                    ctx_str,
                )
                raise AntivirusScanError(
                    message=(
                        "Le fichier n'a pas été accepté car sa taille "
                        "dépasse la limite autorisée pour le contrôle antivirus"
                    )
                )

            timeout = custom_timeout_fn(file_size) if custom_timeout_fn is not None else self._timeout
            if custom_timeout_fn is not None:
                logger.info("Timeout personnalisé calculé pour le scan antivirus: %s secondes", timeout)
            logger.debug(
                "Initialisation du socket clamd host=%s port=%s timeout=%s [%s]",
                self._host,
                self._port,
                timeout,
                ctx_str,
            )
            cd = clamd.ClamdNetworkSocket(host=self._host, port=self._port, timeout=timeout)
            with open(file_path, "rb") as f:
                result = cd.instream(f)

            status, virus_name = result.get("stream", ("ERROR", None))

            if status == "OK":
                logger.info("Scan antivirus OK [%s]", ctx_str)
                return

            if status == "FOUND":
                logger.warning("Fichier infecté détecté: %s [%s]", virus_name, ctx_str)
                raise VirusFoundError(virus_name=virus_name)

            # Résultat inattendu (ex: ERROR renvoyé par clamd)
            logger.error("Résultat antivirus non conforme: status=%s [%s]", status, ctx_str)
            raise AntivirusScanError(
                message="Le fichier n'a pas été accepté car le contrôle antivirus a retourné un résultat non conforme"
            )

        except AntivirusError:
            raise
        except clamd.ConnectionError as e:
            logger.error("Connexion au service antivirus impossible [%s]", ctx_str, exc_info=e)
            raise AntivirusScanError(message="Le fichier n'a pas été accepté car le service antivirus est indisponible")
        except TimeoutError as e:
            logger.error("Timeout lors du scan antivirus [%s]", ctx_str, exc_info=e)
            raise AntivirusScanError(message="Le fichier n'a pas été accepté car le contrôle antivirus a expiré")
        except OSError as e:
            logger.error("Erreur d'E/S lors de la lecture du fichier pour le scan [%s]", ctx_str, exc_info=e)
            raise AntivirusScanError(
                message="Le fichier n'a pas été accepté en raison d'une erreur lors du contrôle antivirus"
            )
        except Exception as e:
            logger.error("Erreur inattendue lors du scan antivirus [%s]", ctx_str, exc_info=e)
            raise AntivirusScanError(
                message="Le fichier n'a pas été accepté en raison d'une erreur lors du contrôle antivirus"
            )
