"""

Revision ID: 20240212_cp_orphelins
Revises: 20240122_france2030
Create Date: 2024-02-01 16:46:01.020809

"""
from pathlib import Path
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240212_cp_orphelins"
down_revision = "20240122_france2030"
branch_labels = None
depends_on = None

_data_folder = Path(__file__).resolve().parent / __name__

new_views = ["flatten_orphan_cp", "_flatten_financial_lines"]
views_to_restore_on_downgrade = ["_flatten_financial_lines"]
views_to_delete_on_downgrade = ["flatten_orphan_cp"]
materialized_views_to_refresh = ["flatten_financial_lines"]


def upgrade():
    for view in new_views:
        print(f"Création de la vue {view}")
        op.execute(_new_filecontent(f"{view}.sql"))

    _refresh_materialized_views()


def downgrade():
    for view in views_to_restore_on_downgrade:
        print(f"Restaure l'ancienne version de {view}")
        op.execute(_old_filecontent(f"{view}.sql"))

    for view in views_to_delete_on_downgrade:
        print(f"Drop de la vue {view}")
        op.execute(f"DROP VIEW IF EXISTS public.{view}")

    _refresh_materialized_views()


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
