"""empty message

Revision ID: 20250730_programmes_sync_grist
Revises: 20250718_fix_join_qpv_commune
Create Date: 2025-07-30 01:38:47.029059

"""
from alembic import op
import sqlalchemy as sa
import logging

# revision identifiers, used by Alembic.
revision = '20250730_programmes_sync_grist'
down_revision = '20250718_fix_join_qpv_commune'
branch_labels = None
depends_on = None





def upgrade_():
    with op.batch_alter_table('ref_theme', schema=None) as batch_op:
        batch_op.add_column(sa.Column('code', sa.String(), nullable=True))
        batch_op.create_unique_constraint('ref_theme_code_unique', ['code'])

    with op.batch_alter_table('ref_code_programme', schema=None) as batch_op:
        batch_op.add_column(sa.Column('code_theme', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('grist_row_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('is_deleted', sa.Boolean(), server_default='FALSE', nullable=True))
        batch_op.add_column(sa.Column('synchro_grist_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key('code_theme_fkey', 'ref_theme', ['code_theme'], ['code'])
        batch_op.create_foreign_key('synchro_grist_id_fkey', 'synchro_grist', ['synchro_grist_id'], ['id'])
        batch_op.create_unique_constraint('ref_code_programme_grist_row_id_key', ['grist_row_id'])

    conn = op.get_bind()
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MTA' WHERE id = 1; -- Ecologie, développement et mobilité durables"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MVA' WHERE id = 2; -- Cohésion des territoires"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MTR' WHERE id = 4; -- Transformation et fonctions publiques"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MTB' WHERE id = 5; -- Travail et emploi"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MPR' WHERE id = 6; -- Plan de relance"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MSF' WHERE id = 8; -- Sport, jeunesse et vie associative"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MSE' WHERE id = 9; -- Solidarité, insertion et égalité des chances"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MSB' WHERE id = 10; -- Sécurités"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MSA' WHERE id = 11; -- Santé"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MRC' WHERE id = 12; -- Relations avec les collectivités locales"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MAV' WHERE id = 13; -- Investissements d'avenir"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MAC' WHERE id = 14; -- Agriculture, alimentation, forêt et affaires rurales"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MAB' WHERE id = 15; -- Administration générale et territoriale de l'Etat"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MGA' WHERE id = 16; -- Gestion des finances publiques"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MMA' WHERE id = 17; -- Médias, livre et industries culturelles"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MRD' WHERE id = 18; -- Remboursements et dégrèvements"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MRB' WHERE id = 19; -- Régimes sociaux et de retraite"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MJA' WHERE id = 20; -- Justice"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MIA' WHERE id = 21; -- Immigration, asile et intégration"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MEC' WHERE id = 22; -- Enseignement scolaire"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MDB' WHERE id = 23; -- Economie"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MRA' WHERE id = 24; -- Recherche et enseignement supérieur"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MPC' WHERE id = 25; -- Crédits non répartis"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MMB' WHERE id = 26; -- Anciens combattants, mémoire et liens avec la Nation"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MEB' WHERE id = 27; -- Engagements financiers de l'Etat"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MDC' WHERE id = 28; -- Direction de l'action du Gouvernement"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MOA' WHERE id = 29; -- Outre-mer"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MDA' WHERE id = 30; -- Défense"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MAA' WHERE id = 31; -- Action extérieure de l'Etat"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MAD' WHERE id = 32; -- Aide publique au développement"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MCA' WHERE id = 33; -- Conseil et contrôle de l'Etat"))
    conn.execute(sa.text(f"UPDATE public.ref_theme SET code = 'MCB' WHERE id = 34; -- Culture"))

    res = conn.execute(sa.text("SELECT id, theme FROM public.ref_code_programme ORDER BY id;"))
    rows = res.fetchall()
    for row_bop in rows:
        if row_bop.theme is not None:
            id_theme = int(row_bop.theme)
            res = conn.execute(sa.text(f"SELECT code FROM public.ref_theme WHERE id = :id;"), {"id": id_theme})
            theme = res.fetchone()
            if theme is not None:
                conn.execute(sa.text(f"UPDATE public.ref_code_programme SET code_theme=:code_theme WHERE id = :id;"), { "code_theme": theme.code, "id": row_bop.id })


def downgrade_():
    with op.batch_alter_table('ref_code_programme', schema=None) as batch_op:
        batch_op.drop_constraint('ref_code_programme_grist_row_id_key', type_='unique')
        batch_op.drop_constraint('synchro_grist_id_fkey', type_='foreignkey')
        batch_op.drop_constraint('code_theme_fkey', type_='foreignkey')
        batch_op.drop_column('synchro_grist_id')
        batch_op.drop_column('is_deleted')
        batch_op.drop_column('grist_row_id')
        batch_op.drop_column('code_theme')

    with op.batch_alter_table('ref_theme', schema=None) as batch_op:
        batch_op.drop_constraint('ref_theme_code_unique', type_='unique')
        batch_op.drop_column('code')


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