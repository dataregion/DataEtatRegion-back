"""

Revision ID: 20240325_a_multidb_migration
Revises: 20240304_indices_for_ae_deletion
Create Date: 2024-03-07 10:37:45.052107

"""
from alembic import op
import sqlalchemy as sa
import logging
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20240325_a_multidb_migration"
down_revision = "20240304_indices_for_ae_deletion"
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
    with op.batch_alter_table("preference_users", schema=None) as batch_op:
        batch_op.alter_column(
            "date_creation",
            existing_type=postgresql.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=True,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )
        batch_op.alter_column(
            "dernier_acces",
            existing_type=postgresql.TIMESTAMP(timezone=True),
            type_=sa.DateTime(),
            existing_nullable=True,
        )

    with op.batch_alter_table("share_preference", schema=None) as batch_op:
        batch_op.alter_column(
            "email_send", existing_type=sa.BOOLEAN(), nullable=False, existing_server_default=sa.text("false")
        )

    # ### end Alembic commands ###


def downgrade_settings():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("share_preference", schema=None) as batch_op:
        batch_op.alter_column(
            "email_send", existing_type=sa.BOOLEAN(), nullable=True, existing_server_default=sa.text("false")
        )

    with op.batch_alter_table("preference_users", schema=None) as batch_op:
        batch_op.alter_column(
            "dernier_acces",
            existing_type=sa.DateTime(),
            type_=postgresql.TIMESTAMP(timezone=True),
            existing_nullable=True,
        )
        batch_op.alter_column(
            "date_creation",
            existing_type=sa.DateTime(),
            type_=postgresql.TIMESTAMP(timezone=True),
            existing_nullable=True,
            existing_server_default=sa.text("CURRENT_TIMESTAMP"),
        )

    # ### end Alembic commands ###


def upgrade_demarches_simplifiees():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("types", schema=None) as batch_op:
        batch_op.alter_column("type", existing_type=sa.VARCHAR(), nullable=False)

    # ### end Alembic commands ###


def downgrade_demarches_simplifiees():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("types", schema=None) as batch_op:
        batch_op.alter_column("type", existing_type=sa.VARCHAR(), nullable=True)

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
