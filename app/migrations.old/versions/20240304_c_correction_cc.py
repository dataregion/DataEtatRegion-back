"""

Revision ID: 20240304_c_correction_cc
Revises: 20240304_b_integration_demarches
Create Date: 2024-03-21 09:20:10.087210

"""

from pathlib import Path
from alembic import op


# revision identifiers, used by Alembic.
revision = "20240304_c_correction_cc"
down_revision = "20240304_b_integration_demarches"
branch_labels = None
depends_on = None

_data_folder = Path(__file__).resolve().parent / __name__


def upgrade():
    # Upgrade des vues flatten financial
    for view in ["_flatten_financial_lines", "flatten_orphan_cp", "flatten_ae", "flatten_ademe"]:
        op.execute(f"DROP VIEW IF EXISTS public.{view} CASCADE")
    for view in ["flatten_ademe", "flatten_ae", "flatten_orphan_cp", "_flatten_financial_lines"]:
        print(f"Maj de la vue {view}")
        op.execute(_new_filecontent(f"{view}.sql"))


def downgrade():
    # Downgrade des vues flatten financial
    for view in ["_flatten_financial_lines", "flatten_orphan_cp", "flatten_ae", "flatten_ademe"]:
        op.execute(f"DROP VIEW IF EXISTS public.{view} CASCADE")
    for view in ["flatten_ademe", "flatten_ae", "flatten_orphan_cp", "_flatten_financial_lines"]:
        print(f"Maj de la vue {view}")
        op.execute(_old_filecontent(f"{view}.sql"))


def _new_filecontent(name: str):
    """Get file content from ./`modulename`/new/name"""
    p = _data_folder / "new" / name
    with p.open("r") as f:
        view_str = f.read()
    return view_str


def _old_filecontent(name: str):
    """Get file content from ./`modulename`/new/name"""
    p = _data_folder / "old" / name
    with p.open("r") as f:
        view_str = f.read()
    return view_str
