"""

Revision ID: 20240212_z_correctifs_resana
Revises: 20240212_cp_orphelins
Create Date: 2024-02-07 16:54:15.104315

"""

from pathlib import Path
from alembic import op


# revision identifiers, used by Alembic.
revision = "20240212_z_correctifs_resana"
down_revision = "20240212_cp_orphelins"
branch_labels = None
depends_on = None

views_to_upgrade = [
    "flatten_ademe",
]
materialized_views_to_refresh = ["flatten_financial_lines"]


def upgrade():
    for view in views_to_upgrade:
        print(f"Upgrade de la vue {view}")
        op.execute(_new_filecontent(f"{view}.sql"))

    _refresh_materialized_views()


def downgrade():
    print("Rien à downgrade")
    pass


#####
_data_folder = Path(__file__).resolve().parent / __name__


def _refresh_materialized_views():
    for view in materialized_views_to_refresh:
        print(f"refresh materialized view {view}")
        op.execute(f"REFRESH MATERIALIZED VIEW {view}")


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
