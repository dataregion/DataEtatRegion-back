"""

Revision ID: 20240304_hf_vues_visuterritoires
Revises: 20240304_c_correction_cc
Create Date: 2024-03-05 11:30:33.987308

"""
from pathlib import Path
from alembic import op


# revision identifiers, used by Alembic.
revision = "20240304_hf_vues_visuterritoires"
down_revision = "20240304_c_correction_cc"
branch_labels = None
depends_on = None


_data_folder = Path(__file__).resolve().parent / __name__


def upgrade():
    # Recréation de vues visuterritoire
    print("creating flatten_summarized_ae")
    op.execute(_new_view_vt_flatten_summarized_ae())
    print("creating flatten_summarized_ademe")
    op.execute(_new_view_vt_flatten_summarized_ademe())
    print("creating vues de visu territoire")
    op.execute(_new_views_vt_visuterritoire())


def downgrade():
    print("Nothing to change")


def _new_view_vt_flatten_summarized_ae():
    return _new_filecontent("vt_flatten_summarized_ae.sql")


def _new_view_vt_flatten_summarized_ademe():
    return _new_filecontent("vt_flatten_summarized_ademe.sql")


def _new_views_vt_visuterritoire():
    return _new_filecontent("vt_views_visuterritoire.sql")


def _new_filecontent(name: str):
    """Get file content from ./`modulename`/new/name"""
    p = _data_folder / "new" / name
    with p.open("r") as f:
        view_str = f.read()
    return view_str
