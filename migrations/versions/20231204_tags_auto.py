"""empty message

Revision ID: e87456b0b094
Revises: 20231123_views_in_migration
Create Date: 2023-12-04 16:35:38.071545

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20231204_tags_auto'
down_revision = '20231123_views_in_migration'
branch_labels = None
depends_on = None


def upgrade():
    # Infos communes pour tags PVD & ACV
    with op.batch_alter_table('ref_commune', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_pvd', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('date_pvd', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('is_acv', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('date_acv', sa.Date(), nullable=True))
    
    op.execute("""
        INSERT INTO tags (type, description, enable_rules_auto, display_name)
        VALUES
        ('pvd', 'Petite Ville de Demain', true, 'PVD'),
        ('acv', 'Action cœur de ville', true, 'ACV');
    """)

    # Foreign key on delete cascade
    with op.batch_alter_table('tag_association', schema=None) as batch_op:
        batch_op.drop_constraint('tag_association_tag_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key('tag_association_tag_id_fkey', 'tags', ['tag_id'], ['id'], ondelete='cascade')


def downgrade():
    # Infos communes pour tags PVD & ACV
    with op.batch_alter_table('ref_commune', schema=None) as batch_op:
        batch_op.drop_column('is_pvd')
        batch_op.drop_column('date_pvd')
        batch_op.drop_column('is_acv')
        batch_op.drop_column('date_acv')

    op.execute("DELETE FROM tags WHERE type IN ('pvd', 'acv');")

    # Foreign key on delete cascade
    with op.batch_alter_table('tag_association', schema=None) as batch_op:
        batch_op.drop_constraint('tag_association_tag_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key('tag_association_tag_id_fkey', 'tags', ['tag_id'], ['id'])