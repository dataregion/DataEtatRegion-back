"""
Nom de la table publiée depuis Grist.

Le tableId n'est unique qu'à l'intérieur de son document Grist : deux documents (par exemple deux
copies du modèle « budget ») ont des tables de même tableId. La table publiée porte donc le docId
en suffixe, `<tableId>_<docId>`, pour qu'un document n'écrase jamais les données d'un autre.
"""

import re

from apis.apps.grist_to_superset.exceptions.import_data_exceptions import (
    InvalidGristDocIdException,
    InvalidTableIdException,
    PublishedTableNameTooLongException,
)

# Limite des identifiants PostgreSQL (NAMEDATALEN - 1) : au-delà, Postgres tronque sans erreur,
# et deux noms tronqués peuvent se retrouver identiques
POSTGRES_IDENTIFIER_MAX_LENGTH = 63

# docId de 22 caractères, suivi pour une copie de travail (fork) de « ~<forkId>[~<userId>] »
_DOC_ID_PATTERN = re.compile(r"^[A-Za-z0-9]{22}(~[A-Za-z0-9]+)*$")
_TABLE_ID_PATTERN = re.compile(r"^[A-Za-z0-9_]+$")


def build_published_table_name(table_id: str, doc_id: str) -> str:
    """
    Raises:
        InvalidGristDocIdException: docId absent ou mal formé
        InvalidTableIdException: tableId vide ou contenant des caractères non autorisés
        PublishedTableNameTooLongException: le nom dépasserait la limite des identifiants PostgreSQL
    """
    if not _DOC_ID_PATTERN.match(doc_id):
        raise InvalidGristDocIdException()
    if not _TABLE_ID_PATTERN.match(table_id):
        raise InvalidTableIdException(table_id)
    published_table_name = f"{table_id}_{doc_id}"
    if len(published_table_name) > POSTGRES_IDENTIFIER_MAX_LENGTH:
        raise PublishedTableNameTooLongException(table_id, POSTGRES_IDENTIFIER_MAX_LENGTH - len(doc_id) - 1)
    return published_table_name
