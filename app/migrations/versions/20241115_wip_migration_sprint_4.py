"""20241115_wip_migration

Revision ID: 20241115_wip_migration
Revises: 20241029_hf1_import_appid
Create Date: 2024-10-29 15:27:38.235052

"""
import logging

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '20241115_wip_migration'
down_revision = '20241030_multi_token_ds'
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
    with op.batch_alter_table('preference_users', schema=None) as batch_op:
        batch_op.drop_column('application_host')

    op.create_table('tokens',
                    sa.Column('id', sa.Integer(), nullable=False),
                    sa.Column('nom', sa.String(), nullable=False),
                    sa.Column('token', sa.LargeBinary(), nullable=False),
                    sa.Column('uuid_utilisateur', sa.String(), nullable=False),
                    sa.PrimaryKeyConstraint('id')
                    )
    with op.batch_alter_table('tokens', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_tokens_uuid_utilisateur'), ['uuid_utilisateur'], unique=False)

    # ### end Alembic commands ###


def downgrade_settings():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('preference_users', schema=None) as batch_op:
        batch_op.add_column(sa.Column('application_host', sa.VARCHAR(), server_default=sa.text("''::character varying"),
                                      autoincrement=False, nullable=False))

    with op.batch_alter_table('tokens', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_tokens_uuid_utilisateur'))

    op.drop_table('tokens')

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
