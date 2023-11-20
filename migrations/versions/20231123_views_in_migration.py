"""

Revision ID: 20231123_views_in_migration
Revises: 20231026_fix_tags_case
Create Date: 2023-11-13 14:53:18.871674

"""
from pathlib import Path
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20231123_views_in_migration"
down_revision = "20231026_fix_tags_case"
branch_labels = None
depends_on = None

_data_folder = Path(__file__).resolve().parent / __name__


def upgrade():
    # Views
    _drop_old_view()

    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_ae")
    op.execute(_view_flatten_ae())
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_ademe")
    op.execute(_view_flatten_ademe())

    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_financial_lines")
    op.execute(_view_flatten_financial_lines())

    op.execute("DROP VIEW IF EXISTS public.superset_lignes_financieres")
    op.execute(_view_superset_lignes_financieres())

    # visuterritoire
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_summarized_ae")
    op.execute(_view_vt_flatten_summarized_ae())
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_summarized_ademe")
    op.execute(_view_vt_flatten_summarized_ademe())

    print("On crée les vues visuterritoire. Cela peut être long.")
    op.execute(_views_vt_visuterritoire())

    # PVD
    with op.batch_alter_table('ref_commune', schema=None) as batch_op:
        batch_op.add_column(sa.Column('is_pvd', sa.Boolean(), nullable=True))
        batch_op.add_column(sa.Column('date_pvd', sa.Date(), nullable=True))


def downgrade():
    # Views
    _drop_old_view()

    op.execute("DROP VIEW IF EXISTS public.montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_m_montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_m_summary_annee_geo_type_bop")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_budget_summary")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_flatten_summarized_ademe")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_flatten_summarized_ae")
    op.execute(_old_view_flatten_summarized_ae())

    print("On recrée les anciennes vues visuterritoire. Cela peut être long.")
    op.execute(_views_old_visuterritoire())

    op.execute("DROP VIEW IF EXISTS public.superset_lignes_financieres")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_financial_lines")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_ae")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.flatten_ademe")

    # PVD
    with op.batch_alter_table('ref_commune', schema=None) as batch_op:
        batch_op.drop_column('is_pvd')
        batch_op.drop_column('date_pvd')


def _drop_old_view():
    """Drop les vues qui ont été créées hors migration."""
    op.execute("DROP VIEW IF EXISTS public.montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.m_montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.m_summary_annee_geo_type_bop")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.budget_summary")


def _view_flatten_financial_lines():
    return _filecontent("flatten_financial_lines.sql")


def _view_superset_lignes_financieres():
    return _filecontent("superset_lignes_financieres.sql")


def _view_flatten_ae():
    return _filecontent("flatten_ae.sql")


def _view_flatten_ademe():
    return _filecontent("flatten_ademe.sql")


def _view_vt_flatten_summarized_ae():
    return _filecontent("vt_flatten_summarized_ae.sql")


def _view_vt_flatten_summarized_ademe():
    return _filecontent("vt_flatten_summarized_ademe.sql")


def _old_view_flatten_summarized_ae():
    return _filecontent("old_flatten_summarized_ae.sql")


def _views_vt_visuterritoire():
    return _filecontent("vt_views_visuterritoire.sql")


def _views_old_visuterritoire():
    return _filecontent("old_manual_view_vissuterritoire.sql")


def _filecontent(name: str):
    """Get file content from ./`modulename`/name"""
    p = _data_folder / name
    with p.open("r") as f:
        view_str = f.read()
    return view_str
