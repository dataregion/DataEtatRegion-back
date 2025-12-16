from pydantic import BaseModel
from pathlib import Path

class Config(BaseModel):
    print_sql: bool
    """Flag qui active le paramètre 'echo' de l'engine sqlalchemy"""
    sqlalchemy_database_uri: str
    """Base de données principale"""
    sqlalchemy_database_uri_audit: str
    """Base de données d'audit (utilisée avec le bind)"""
    
    dossier_des_exports: Path
    """Chemin vers le répertoire qui contient les exports utilisateurs."""