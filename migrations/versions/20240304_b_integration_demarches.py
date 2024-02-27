"""empty message

Revision ID: dc2dcf3d1f7f
Revises: 20240212_zzzz_col_username
Create Date: 2024-02-23 17:37:04.977511

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20240304_b_integration_demarches'
down_revision = '20240212_zzzz_col_username'
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE SCHEMA demarches_simplifiees")

    op.create_table(
        "demarches",
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("number"),
        schema="demarches_simplifiees",
    )
    op.create_table(
        "dossiers",
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("demarche_number", sa.Integer(), nullable=False),
        sa.Column("state", sa.String(), nullable=False),
        sa.Column("date_derniere_modification", sa.DateTime(), nullable=False),
        sa.Column("siret", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["demarche_number"], ["demarches_simplifiees.demarches.number"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("number"),
        schema="demarches_simplifiees",
    )
    op.create_table(
        "sections",
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("name"),
        schema="demarches_simplifiees",
    )
    op.create_table(
        "types",
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("type", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("name"),
        schema="demarches_simplifiees",
    )
    op.create_table(
        "donnees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("demarche_number", sa.Integer(), nullable=False),
        sa.Column("section_name", sa.String(), nullable=False),
        sa.Column("type_name", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["demarche_number"], ["demarches_simplifiees.demarches.number"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["section_name"], ["demarches_simplifiees.sections.name"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["type_name"], ["demarches_simplifiees.types.name"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
        schema="demarches_simplifiees",
    )
    op.create_table(
        "valeurs_donnees",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("dossier_number", sa.Integer(), nullable=False),
        sa.Column("donnee_id", sa.Integer(), nullable=False),
        sa.Column("valeur", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["dossier_number"], ["demarches_simplifiees.dossiers.number"], ondelete="cascade"),
        sa.ForeignKeyConstraint(["donnee_id"], ["demarches_simplifiees.donnees.id"], ondelete="cascade"),
        sa.PrimaryKeyConstraint("id"),
        schema="demarches_simplifiees",
    )


def downgrade():
    op.drop_table("valeurs_donnees", schema="demarches_simplifiees")
    op.drop_table("donnees", schema="demarches_simplifiees")
    op.drop_table("types", schema="demarches_simplifiees")
    op.drop_table("sections", schema="demarches_simplifiees")
    op.drop_table("dossiers", schema="demarches_simplifiees")
    op.drop_table("demarches", schema="demarches_simplifiees")
    op.execute("DROP SCHEMA demarches_simplifiees")
