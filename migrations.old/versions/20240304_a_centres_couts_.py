"""

Revision ID: 20240304_a_centres_couts
Revises: 20240212_zzzz_col_username
Create Date: 2024-02-22 15:20:10.087210

"""
from pathlib import Path
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240304_a_centres_couts"
down_revision = "20240212_zzzz_col_username"
branch_labels = None
depends_on = None

_data_folder = Path(__file__).resolve().parent / __name__


def _rattrapage_upgrade():
    """Upgrade de rattrapage de migration oubliées précédement"""

    with op.batch_alter_table("financial_ae", schema=None) as batch_op:
        batch_op.drop_column("montant")

    with op.batch_alter_table("financial_cp", schema=None) as batch_op:
        batch_op.drop_constraint("financial_cp_id_ae_fkey", type_="foreignkey")
        batch_op.create_foreign_key("financial_cp_id_ae_fkey", "financial_ae", ["id_ae"], ["id"], ondelete="cascade")

    with op.batch_alter_table("ref_region", schema=None) as batch_op:
        batch_op.add_column(sa.Column("created_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("updated_at", sa.DateTime(), nullable=True))


def _rattrapage_downgrade():
    """Downgrade de rattrapage de migration oubliées précédement"""

    with op.batch_alter_table("ref_region", schema=None) as batch_op:
        batch_op.drop_column("updated_at")
        batch_op.drop_column("created_at")

    with op.batch_alter_table("financial_cp", schema=None) as batch_op:
        batch_op.drop_constraint("financial_cp_id_ae_fkey", type_="foreignkey")
        batch_op.create_foreign_key("financial_cp_id_ae_fkey", "financial_ae", ["id_ae"], ["id"])

    with op.batch_alter_table("financial_ae", schema=None) as batch_op:
        batch_op.add_column(
            sa.Column(
                "montant",
                sa.DOUBLE_PRECISION(precision=53),
                server_default=sa.text("0"),
                autoincrement=False,
                nullable=True,
            )
        )


def upgrade():
    _rattrapage_upgrade()

    # Upgrade des vues flatten financial
    for view in ["flatten_ademe", "flatten_ae", "flatten_orphan_cp", "_flatten_financial_lines"]:
        print(f"Maj de la vue {view}")
        op.execute(_new_filecontent(f"{view}.sql"))


def downgrade():
    _rattrapage_downgrade()


def _new_filecontent(name: str):
    """Get file content from ./`modulename`/new/name"""
    p = _data_folder / "new" / name
    with p.open("r") as f:
        view_str = f.read()
    return view_str


def _old_filecontent(name: str):
    """Get file content from ./`modulename`/old/name"""
    p = _data_folder / "old" / name
    with p.open("r") as f:
        view_str = f.read()
    return view_str
