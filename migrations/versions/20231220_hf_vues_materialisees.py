"""

Revision ID: 20231220_hf_vues_materialisees
Revises: 20231204_tags_auto
Create Date: 2023-12-20 14:30:33.987308

"""
from pathlib import Path
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20231220_hf_vues_materialisees"
down_revision = "20231204_tags_auto"
branch_labels = None
depends_on = None


_data_folder = Path(__file__).resolve().parent / __name__


def upgrade():
    _drop_old_views()
    # ### end Alembic commands ###

    # Recrée les vues
    print("creating flatten_ae")
    op.execute(_new_view_flatten_ae())
    print("creating flatten_ademe")
    op.execute(_new_view_flatten_ademe())

    print("creating flatten_financial_lines")
    op.execute(_new_view_flatten_financial_lines())
    print("creating superset_lignes_financieres")
    op.execute(_new_view_superset_lignes_financieres())

    # visuterritoire
    print("creating flatten_summarized_ae")
    op.execute(_new_view_vt_flatten_summarized_ae())
    print("creating flatten_summarized_ademe")
    op.execute(_new_view_vt_flatten_summarized_ademe())

    print("creating vues de visu territoire")
    op.execute(_new_views_vt_visuterritoire())


def downgrade():
    _drop_new_views()

    # Recrée les vues
    print("creating flatten_ae")
    op.execute(_old_view_flatten_ae())
    print("creating flatten_ademe")
    op.execute(_old_view_flatten_ademe())

    print("creating flatten_financial_lines")
    op.execute(_old_view_flatten_financial_lines())
    print("creating superset_lignes_financieres")
    op.execute(_old_view_superset_lignes_financieres())

    # visuterritoire
    print("creating flatten_summarized_ae")
    op.execute(_old_view_vt_flatten_summarized_ae())
    print("creating flatten_summarized_ademe")
    op.execute(_old_view_vt_flatten_summarized_ademe())

    print("creating vues de visu territoire")
    op.execute(_old_views_vt_visuterritoire())


def _drop_old_views():
    #
    # Drop de toutes les vues
    #
    print("Drop de toutes les vues")
    op.execute("DROP VIEW IF EXISTS public.montant_par_niveau_bop_annee_type")
    op.execute("DROP VIEW IF EXISTS public.superset_lignes_financieres")

    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_m_montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_m_summary_annee_geo_type_bop")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_budget_summary")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_flatten_summarized_ademe")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_flatten_summarized_ae")

    #
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_financial_lines")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_ademe")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_ae")


def _drop_new_views():
    #
    # Drop de toutes les vues
    #
    print("Drop de toutes les vues")
    op.execute("DROP VIEW IF EXISTS public.montant_par_niveau_bop_annee_type")
    op.execute("DROP VIEW IF EXISTS public.superset_lignes_financieres")

    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_m_montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_m_summary_annee_geo_type_bop")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_budget_summary")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_flatten_summarized_ademe")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_flatten_summarized_ae")

    #
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_financial_lines")
    op.execute("DROP VIEW IF EXISTS public._flatten_financial_lines")
    op.execute("DROP VIEW IF EXISTS public.flatten_ademe")
    op.execute("DROP VIEW IF EXISTS public.flatten_ae")


def _old_view_flatten_ae():
    return _old_filecontent("flatten_ae.sql")


def _old_view_flatten_ademe():
    return _old_filecontent("flatten_ademe.sql")


def _old_view_flatten_financial_lines():
    return _old_filecontent("flatten_financial_lines.sql")


def _old_view_superset_lignes_financieres():
    return _old_filecontent("superset_lignes_financieres.sql")


def _old_view_vt_flatten_summarized_ae():
    return _old_filecontent("vt_flatten_summarized_ae.sql")


def _old_view_vt_flatten_summarized_ademe():
    return _old_filecontent("vt_flatten_summarized_ademe.sql")


def _old_views_vt_visuterritoire():
    return _old_filecontent("vt_views_visuterritoire.sql")


def _new_view_flatten_ae():
    return _new_filecontent("flatten_ae.sql")


def _new_view_flatten_ademe():
    return _new_filecontent("flatten_ademe.sql")


def _new_view_flatten_financial_lines():
    return _new_filecontent("flatten_financial_lines.sql")


def _new_view_superset_lignes_financieres():
    return _new_filecontent("superset_lignes_financieres.sql")


def _new_view_vt_flatten_summarized_ae():
    return _new_filecontent("vt_flatten_summarized_ae.sql")


def _new_view_vt_flatten_summarized_ademe():
    return _new_filecontent("vt_flatten_summarized_ademe.sql")


def _new_views_vt_visuterritoire():
    return _new_filecontent("vt_views_visuterritoire.sql")


def _old_filecontent(name: str):
    """Get file content from ./`modulename`/old/name"""
    p = _data_folder / "old" / name
    with p.open("r") as f:
        view_str = f.read()
    return view_str


def _new_filecontent(name: str):
    """Get file content from ./`modulename`/new/name"""
    p = _data_folder / "new" / name
    with p.open("r") as f:
        view_str = f.read()
    return view_str
