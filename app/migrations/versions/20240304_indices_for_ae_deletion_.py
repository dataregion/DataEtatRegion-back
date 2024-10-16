"""

Revision ID: 20240304_indices_for_ae_deletion
Revises: 
Create Date: 2024-03-05 18:34:45.538113

"""
import logging

# revision identifiers, used by Alembic.
revision = "20240304_indices_for_ae_deletion"
down_revision = None
branch_labels = None
depends_on = None


#
# C'est un script de migration vide qui vise à faire le lien entre les anciens
# scripts de migration et les nouveaux.
#


# ###############################################################################
# Boilerplate
#
def _call(name):
    if name not in globals():
        logging.warning(f"Pas de fonction: '{name}'. la migration sera ignorée")
    else:
        globals()[name]()


def upgrade(engine_name):
    fn_name = f"upgrade_{engine_name}"
    _call(fn_name)


def downgrade(engine_name):
    fn_name = f"downgrade_{engine_name}"
    _call(fn_name)


# ###############################################################################
