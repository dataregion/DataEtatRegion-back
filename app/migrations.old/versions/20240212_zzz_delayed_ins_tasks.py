"""empty message

Revision ID: 20240212_zzz_table_delayed_insert_tasks
Revises: 20240212_zz_ae_montant_cascade
Create Date: 2024-02-09 16:22:38.951571

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240212_zzz_delayed_ins_tasks"
down_revision = "20240212_zz_ae_montant_cascade"
branch_labels = None
depends_on = None


def upgrade():
    # Création table de sauvegarde des tâches d'insertion à éxécuter
    op.create_table(
        "audit_insert_financial_tasks",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("fichier_ae", sa.String(), nullable=False),
        sa.Column("fichier_cp", sa.String(length=255), nullable=False),
        sa.Column("source_region", sa.String(length=255), nullable=False),
        sa.Column("annee", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="audit",
    )


def downgrade():
    # Suppression table de sauvegarde des tâches d'insertion à éxécuter
    op.drop_table("audit_insert_financial_tasks", schema="audit")
