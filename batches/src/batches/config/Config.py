from pydantic import BaseModel
from pathlib import Path

class GristConfig(BaseModel):
    database_url: str
    """Base de donnée SQL pour le backoffice grist"""
    serveur_url: str
    """L'url de grist"""
    token_scim: str
    """Le token de l'utilisateur SCIM"""


class RemoteFilesConfig(BaseModel):
    donnees_qpv_entreprises: str
    """URL du fichier contenant le lien entre QPV et SIRET"""


class Config(BaseModel):
    print_sql: bool
    """Flag qui active le paramètre 'echo' de l'engine sqlalchemy"""
    sqlalchemy_database_uri: str
    """Base de données principale"""
    sqlalchemy_database_uri_audit: str
    """Base de données d'audit (utilisée avec le bind)"""
    
    dossier_des_exports: Path
    """Chemin vers le répertoire qui contient les exports utilisateurs."""
    dossier_des_telechargements: Path
    """Chemin vers le répertoire qui contient les fichiers téléchargés de l'extérieur."""
    
    grist: GristConfig
    """Configuration pour le client grist"""

    cached_remote_files_url: RemoteFilesConfig
    """Configuration des URL des fichiers distants à télécharger"""