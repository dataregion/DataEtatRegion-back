"""empty message

Revision ID: 66b8c45a2202
Revises: 20231026_fix_tags_case
Create Date: 2023-11-06 09:31:44.306442

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '66b8c45a2202'
down_revision = '20231026_fix_tags_case'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('ref_commune', schema=None) as batch_op:
        batch_op.add_column(sa.Column('date_signature_pvd', sa.Date(), nullable=True))


def downgrade():
    with op.batch_alter_table('ref_commune', schema=None) as batch_op:
        batch_op.drop_column('date_signature_pvd')
