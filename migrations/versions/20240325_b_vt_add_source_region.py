"""

Revision ID: 20240325_b_vt_add_source_region
Revises: 20240325_a_multidb_migration
Create Date: 2024-03-13 12:00:45.052107

"""
from pathlib import Path
from alembic import op
import logging

# revision identifiers, used by Alembic.
revision = "20240325_b_vt_add_source_region"
down_revision = "20240325_a_multidb_migration"
branch_labels = None
depends_on = None

_data_folder = Path(__file__).resolve().parent / __name__


def upgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    op.execute("DROP VIEW IF EXISTS public.montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_m_montant_par_niveau_bop_annee_type")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_m_summary_annee_geo_type_bop")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS public.vt_budget_summary")

    op.execute(_filecontent("vt_views_visuterritoire.sql"))
    # ### end Alembic commands ###


def downgrade_():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


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


def upgrade_demarches_simplifiees():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade_demarches_simplifiees():
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

def _filecontent(name: str):
    """Get file content from ./`modulename`/name"""
    p = _data_folder / name
    with p.open("r") as f:
        view_str = f.read()
    return view_str
