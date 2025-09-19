"""
Revision ID: 20250918_vues_pour_smart
Revises: 20250730_programmes_sync_grist
Create Date: 2025-09-18 10:48:35.152149
"""

from alembic import op
import logging


# revision identifiers, used by Alembic.
revision = '20250918_vues_pour_smart'
down_revision = '20250730_programmes_sync_grist'
branch_labels = None
depends_on = None





def upgrade_():
    op.execute(
        """
        CREATE VIEW _superset_lignes_financieres_52 AS
        SELECT * FROM superset_lignes_financieres
        WHERE source_region = '52';

        CREATE MATERIALIZED VIEW IF NOT EXISTS superset_lignes_financieres_52 AS
        SELECT * FROM _superset_lignes_financieres_52;
        """
    )


def downgrade_():
    op.execute(
        """
        DROP MATERIALIZED VIEW IF EXISTS superset_lignes_financieres_52;
        DROP VIEW IF EXISTS _superset_lignes_financieres_52;
        """
    )


def upgrade_audit():
    pass


def downgrade_audit():
    pass


def upgrade_settings():
    pass


def downgrade_settings():
    pass


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