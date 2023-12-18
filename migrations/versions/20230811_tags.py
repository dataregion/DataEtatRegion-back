"""empty message

Revision ID: 4af5d1e78b3e
Revises: 72cb30957126
Create Date: 2023-08-11 17:00:52.214762

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "4af5d1e78b3e"
down_revision = "72cb30957126"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    table_tags = op.create_table(
        "tags",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("type", sa.String(length=255), nullable=False),
        sa.Column("value", sa.String(length=255), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("enable_rules_auto", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("type", "value", name="uq_type_value_tags"),
    )
    op.create_table(
        "tag_association",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tag_id", sa.Integer(), nullable=False),
        sa.Column("auto_applied", sa.Boolean(), nullable=False, default=False),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.Column("ademe", sa.Integer(), nullable=True),
        sa.Column("financial_ae", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["financial_ae"], ["financial_ae.id"]),
        sa.ForeignKeyConstraint(["ademe"], ["ademe.id"]),
        sa.ForeignKeyConstraint(
            ["tag_id"],
            ["tags.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_check_constraint(
        "line_fks_xor", table_name="tag_association", condition="num_nonnulls(ademe, financial_ae) = 1"
    )

    data_to_insert = [
        {
            "type": "Fond vert",
            "value": None,
            "description": 'La ligne est taguée Fonds vert si le libellé de son champ Programme est "380-".',
            "enable_rules_auto": True,
        },
        {
            "type": "Relance",
            "value": None,
            "description": 'La ligne est taguée France Relance si le libellé de son champ Thème est "France Relance".',
            "enable_rules_auto": True,
        },
        {
            "type": "CPER",
            "value": "2015-20",
            "description": 'La ligne est taguée CPER si le champ "Contrat plan État-région" n’est pas nul (NULL) ou non affecté (NA), selon l’année.',
            "enable_rules_auto": True,
        },
        {
            "type": "CPER",
            "value": "2021-27",
            "description": 'La ligne est taguée CPER si le champ "Contrat plan État-région" n’est pas nul (NULL) ou non affecté (NA), selon l’année.',
            "enable_rules_auto": True,
        },
        {
            "type": "DETR",
            "value": None,
            "description": 'La ligne est taguée DETR si le libellé de son champ Référentiel Programmation est "DETR".',
            "enable_rules_auto": True,
        },
    ]
    op.bulk_insert(table_tags, data_to_insert)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("tag_association")
    op.drop_table("tags")
    # ### end Alembic commands ###
