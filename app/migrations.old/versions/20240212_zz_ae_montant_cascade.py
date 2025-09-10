"""

Revision ID: 20240212_zz_ae_montant_cascade
Revises: 20240212_z_correctifs_resana
Create Date: 2024-02-08 16:54:15.104315

"""

from alembic import op


# revision identifiers, used by Alembic.
revision = "20240212_zz_ae_montant_cascade"
down_revision = "20240212_z_correctifs_resana"
branch_labels = None
depends_on = None


def upgrade():
    # Delete cascade entre AE et montant
    with op.batch_alter_table("montant_financial_ae", schema=None) as batch_op:
        batch_op.drop_constraint("montant_financial_ae_id_financial_ae_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "montant_financial_ae_id_financial_ae_fkey", "financial_ae", ["id_financial_ae"], ["id"], ondelete="cascade"
        )


def downgrade():
    # Pas de delete cascade entre AE et montant
    with op.batch_alter_table("montant_financial_ae", schema=None) as batch_op:
        batch_op.drop_constraint("montant_financial_ae_id_financial_ae_fkey", type_="foreignkey")
        batch_op.create_foreign_key(
            "montant_financial_ae_id_financial_ae_fkey", "financial_ae", ["id_financial_ae"], ["id"]
        )
