"""empty message

Revision ID: 20250124_b_cascade_del
Revises: 202500107_a_cascade_del
Create Date: 2025-01-23 17:42:22.293699

"""
from alembic import op
import logging

# revision identifiers, used by Alembic.
revision = '20250124_b_cascade_del'
down_revision = '202500107_a_cascade_del'
branch_labels = None
depends_on = None





def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_audit():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_audit():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_settings():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_settings():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_demarches_simplifiees():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reconciliations', schema=None) as batch_op:
        batch_op.drop_constraint('reconciliations_dossier_number_fkey', type_='foreignkey')
        batch_op.create_foreign_key('reconciliations_dossier_number_fkey', 'dossiers', ['dossier_number'], ['number'], ondelete='CASCADE')

    # ### end Alembic commands ###


def downgrade_demarches_simplifiees():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('reconciliations', schema=None) as batch_op:
        batch_op.drop_constraint('reconciliations_dossier_number_fkey', type_='foreignkey')
        batch_op.create_foreign_key('reconciliations_dossier_number_fkey', 'dossiers', ['dossier_number'], ['number'])

    # ### end Alembic commands ###


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