from pydantic import BaseModel, Field


class AntivirusConfig(BaseModel):
    enabled: bool = Field(default=True, description="Active ou désactive le scan antivirus")
    host: str = Field(default="clamav", description="Hôte du service ClamAV (clamd)")
    port: int = Field(default=3310, description="Port TCP du démon clamd")
    timeout: int = Field(default=60, description="Timeout en secondes pour la connexion clamd")
    max_file_size_bytes: int = Field(
        default=25 * 1024 * 1024,
        description="Taille maximale autorisée pour un fichier scanné par l'antivirus (en octets)",
    )
