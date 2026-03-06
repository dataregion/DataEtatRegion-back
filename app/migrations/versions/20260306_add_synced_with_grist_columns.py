"""add synced_with_grist columns

Revision ID: 20260306_add_synced_with_grist_columns
Revises: 20260302_update_views_add_cdpt_py
Create Date: 2026-03-06 15:31:02.000000

"""
from alembic import op
import sqlalchemy as sa
import logging

# revision identifiers, used by Alembic.
revision = '20260306_add_synced_with_grist_columns'
down_revision = '20260302_update_views_add_cdpt_py'
branch_labels = None
depends_on = None


def upgrade_():
    tables = [
        'ref_ministere', 'ref_localisation_interministerielle',
        'ref_programmation', 'ref_domaine_fonctionnel', 'ref_centre_couts',
        'ref_groupe_marchandise', 'ref_fournisseur_titulaire', 'ref_categorie_juridique',
        'ref_region', 'ref_departement', 'ref_qpv', 'ref_arrondissement',
        'nomenclature_france_2030'
    ]

    for tbl in tables:
        with op.batch_alter_table(tbl, schema=None) as batch_op:
            batch_op.add_column(sa.Column('grist_row_id', sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True))
            batch_op.add_column(sa.Column('synchro_grist_id', sa.Integer(), nullable=True))
            # create fk to synchro_grist
            batch_op.create_foreign_key(f'{tbl}_synchro_grist_id_fkey', 'synchro_grist', ['synchro_grist_id'], ['id'])
            # unique constraint on grist_row_id where appropriate
            try:
                batch_op.create_unique_constraint(f'{tbl}_grist_row_id_key', ['grist_row_id'])
            except Exception:
                # some tables may already have similar constraints
                logging.warning(f"Could not create unique constraint on {tbl}.grist_row_id")


def downgrade_():
    tables = [
        'ref_ministere', 'ref_localisation_interministerielle',
        'ref_programmation', 'ref_domaine_fonctionnel', 'ref_centre_couts',
        'ref_groupe_marchandise', 'ref_fournisseur_titulaire', 'ref_categorie_juridique',
        'ref_region', 'ref_departement', 'ref_qpv', 'ref_arrondissement',
        'nomenclature_france_2030'
    ]

    for tbl in tables:
        with op.batch_alter_table(tbl, schema=None) as batch_op:
            try:
                batch_op.drop_constraint(f'{tbl}_grist_row_id_key', type_='unique')
            except Exception:
                logging.warning(f"Could not drop unique constraint for {tbl}.grist_row_id")
            try:
                batch_op.drop_constraint(f'{tbl}_synchro_grist_id_fkey', type_='foreignkey')
            except Exception:
                logging.warning(f"Could not drop fk for {tbl}.synchro_grist_id")
            batch_op.drop_column('synchro_grist_id')
            batch_op.drop_column('is_deleted')
            batch_op.drop_column('grist_row_id')


def upgrade_audit():
    pass


def downgrade_audit():
    pass


def upgrade_settings():
    pass


def downgrade_settings():
    pass


def upgrade_demarches_simplifiees():
    pass


def downgrade_demarches_simplifiees():
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
