"""empty message

Revision ID: edc5f93432df
Revises: cf35dd89ce53
Create Date: 2023-09-29 10:45:42.330641

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "edc5f93432df"
down_revision = "cf35dd89ce53"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("financial_ae", schema=None) as batch_op:
        batch_op.add_column(sa.Column("date_replication", sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("financial_ae", schema=None) as batch_op:
        batch_op.drop_column("date_replication")
    # ### end Alembic commands ###
