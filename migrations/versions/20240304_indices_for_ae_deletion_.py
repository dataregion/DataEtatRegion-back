"""

Revision ID: 20240304_indices_for_ae_deletion
Revises: 20240304_hf_vues_visuterritoires
Create Date: 2024-03-05 15:11:13.784986

"""
from alembic import op


# revision identifiers, used by Alembic.
revision = "20240304_indices_for_ae_deletion"
down_revision = "20240304_hf_vues_visuterritoires"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("financial_cp", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_financial_cp_id_ae"), ["id_ae"], unique=False)

    with op.batch_alter_table("montant_financial_ae", schema=None) as batch_op:
        batch_op.create_index(batch_op.f("ix_montant_financial_ae_id_financial_ae"), ["id_financial_ae"], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table("montant_financial_ae", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_montant_financial_ae_id_financial_ae"))

    with op.batch_alter_table("financial_cp", schema=None) as batch_op:
        batch_op.drop_index(batch_op.f("ix_financial_cp_id_ae"))

    # ### end Alembic commands ###
