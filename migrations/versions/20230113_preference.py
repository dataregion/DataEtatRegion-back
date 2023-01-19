"""empty message

Revision ID: b1cf93401c22
Revises: 20221209_view_montant
Create Date: 2023-01-16 15:22:18.828504

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20230113_preference'
down_revision = '20221209_view_montant'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute('CREATE SCHEMA if not exists settings')


    op.create_table('preference_users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('uuid', postgresql.UUID(as_uuid=True), nullable=False),
    sa.Column('username', sa.String(), nullable=False),
    sa.Column('name', sa.String(), nullable=False),
    sa.Column('filters', sa.JSON(), nullable=False),
    sa.Column('options', sa.JSON(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    schema='settings'
    )
    op.create_table('share_preference',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('preference_id', sa.Integer(), nullable=True),
    sa.Column('shared_username_email', sa.String(), nullable=False),
    sa.ForeignKeyConstraint(['preference_id'], ['settings.preference_users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    schema='settings'
    )
    # ### end Alembic commands ###


def downgrade():
    op.drop_table('share_preference', schema='settings')
    op.drop_table('preference_users', schema='settings')

    op.execute('DROP SCHEMA settings')
    # ### end Alembic commands ###
