""" Suppression superset_data_qpv + intégration à flatten_financial_lines

Revision ID: 20250312_vue_lieu_action
Revises: 20250314_index_performance_vue
Create Date: 2024-10-07 11:18:31.381807

"""

from alembic import op
import logging
from pathlib import Path

# revision identifiers, used by Alembic.
revision = "20250314_vue_lieu_action"
down_revision = "20250314_index_performance_vue"
branch_labels = None
depends_on = None


_data_folder = Path(__file__).resolve().parent / __name__


def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    logging.info("=== Dropping views ===")
    op.execute("DROP INDEX IF EXISTS idx_ffl_codes_qpv")
    op.execute("DROP VIEW IF EXISTS public.superset_data_qpv")
    op.execute("DROP VIEW IF EXISTS public.montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vt_m_montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vt_m_summary_annee_geo_type_bop")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vt_budget_summary")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vt_flatten_summarized_ademe")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vt_flatten_summarized_ae")
    op.execute("DROP VIEW IF EXISTS public.superset_lignes_financieres")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS flatten_financial_lines")
    op.execute("DROP VIEW IF EXISTS public._flatten_financial_lines")
    op.execute("DROP VIEW IF EXISTS public.flatten_orphan_cp")
    op.execute("DROP VIEW IF EXISTS public.flatten_ademe")
    op.execute("DROP VIEW IF EXISTS public.flatten_ae")

    logging.info("=== Recreating views ===")
    op.execute(_new_filecontent("flatten_ae.sql"))
    op.execute(_new_filecontent("flatten_ademe.sql"))
    op.execute(_new_filecontent("flatten_orphan_cp.sql"))
    op.execute(_new_filecontent("flatten_financial_lines.sql"))
    op.execute(_new_filecontent("materialized_flatten_financial_lines.sql"))
    op.execute(_new_filecontent("superset_lignes_financieres.sql"))
    op.execute(_new_filecontent("vt_flatten_summarized_ae.sql"))
    op.execute(_new_filecontent("vt_flatten_summarized_ademe.sql"))
    op.execute(_new_filecontent("vt_budget_summary.sql"))
    op.execute(_new_filecontent("vt_m_summary_annee_geo_type_bop.sql"))
    op.execute(_new_filecontent("vt_m_montant_par_niveau_bop_annee_type.sql"))
    op.execute(_new_filecontent("montant_par_niveau_bop_annee_type.sql"))


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    logging.info("=== Dropping views ===")
    op.execute("DROP VIEW IF EXISTS public.montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vt_m_montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vt_m_summary_annee_geo_type_bop")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vt_budget_summary")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vt_flatten_summarized_ademe")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS vt_flatten_summarized_ae")
    op.execute("DROP VIEW IF EXISTS public.superset_lignes_financieres")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS flatten_financial_lines")
    op.execute("DROP VIEW IF EXISTS public._flatten_financial_lines")
    op.execute("DROP VIEW IF EXISTS public.flatten_orphan_cp")
    op.execute("DROP VIEW IF EXISTS public.flatten_ademe")
    op.execute("DROP VIEW IF EXISTS public.flatten_ae")

    logging.info("=== Recreating views ===")
    op.execute(_old_filecontent("flatten_ae.sql"))
    op.execute(_old_filecontent("flatten_ademe.sql"))
    op.execute(_old_filecontent("flatten_orphan_cp.sql"))
    op.execute(_old_filecontent("flatten_financial_lines.sql"))
    op.execute(_old_filecontent("materialized_flatten_financial_lines.sql"))
    op.execute(_old_filecontent("superset_lignes_financieres.sql"))
    op.execute(_old_filecontent("vt_flatten_summarized_ae.sql"))
    op.execute(_old_filecontent("vt_flatten_summarized_ademe.sql"))
    op.execute(_old_filecontent("vt_budget_summary.sql"))
    op.execute(_old_filecontent("vt_m_summary_annee_geo_type_bop.sql"))
    op.execute(_old_filecontent("vt_m_montant_par_niveau_bop_annee_type.sql"))
    op.execute(_old_filecontent("montant_par_niveau_bop_annee_type.sql"))
    
    logging.info("=== Recreating view superset_data_qpv ===")
    op.execute(_old_filecontent("v_superset_data_qpv.sql"))


def upgrade_audit():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_audit():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def upgrade_settings():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_settings():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


# ###############################################################################
# Boilerplate
#
def _call(name):
    if name not in globals():
        logging.warning(f"Pas de fonction: '{name}'. la migration sera ignorée")
    else:
        globals()[name]()


def upgrade(engine_name):
    fn_name = f"upgrade_{engine_name}"
    _call(fn_name)


def downgrade(engine_name):
    fn_name = f"downgrade_{engine_name}"
    _call(fn_name)


# ###############################################################################
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
