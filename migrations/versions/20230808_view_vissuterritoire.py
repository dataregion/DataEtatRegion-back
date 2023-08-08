"""empty message

Revision ID: cf35dd89ce53
Revises: d1a470f3416f
Create Date: 2023-08-08 14:02:11.303706

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "cf35dd89ce53"
down_revision = "d1a470f3416f"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    _drop_old_view()

    m_view_ae = """ CREATE MATERIALIZED VIEW financial_ae_summary_by_commune AS 
           SELECT  
               DISTINCT(fce.id),
               MAX(fce.annee) as annee, 
               SUM(mce.montant) as montant_ae, 
               fce.programme, 
               rc.code as code_commune,
               rc.code_departement,
               rc.code_crte,
               rc.code_epci,
               rcj.type AS "categorie_juridique"
           FROM "financial_ae" fce 
           LEFT JOIN montant_financial_ae mce ON fce.id = mce.id_financial_ae
           LEFT JOIN ref_siret rs ON fce.siret = rs.code 
           LEFT JOIN ref_commune rc ON rs.code_commune = rc.code 
           LEFT JOIN ref_categorie_juridique rcj ON rs.categorie_juridique = rcj.code
           WHERE rc.code IS NOT NULL 
           GROUP BY fce.id, rc.id, rcj.type;"""
    op.execute(m_view_ae)

    index_m_view_ae = """CREATE INDEX idx_groupby_montant_ae ON financial_ae_summary_by_commune 
                       (annee, programme, categorie_juridique, code_commune, montant_ae);"""
    op.execute(index_m_view_ae)

    m_view_cp = """CREATE MATERIALIZED VIEW financial_cp_summary_by_commune AS 
               SELECT 
                   fcp.id,
                   fcp.annee,
                   fcp.montant as montant_cp,
                   fcp.programme,
                   rc.code  as code_commune,
                   rc.code_departement,
                   rc.code_crte,
                   rc.code_epci,
                   rcj."type" AS "categorie_juridique"
               FROM "financial_cp" fcp
               LEFT JOIN "ref_siret" rs ON fcp."siret" = rs."code"
               LEFT JOIN "ref_commune" rc ON rs."code_commune" = rc."code"
               LEFT JOIN "ref_categorie_juridique" rcj ON rs."categorie_juridique" = rcj."code"
               WHERE rc.code IS NOT NULL """
    op.execute(m_view_cp)

    index_m_view_cp = """ CREATE INDEX idx_groupby_montant_cp ON financial_cp_summary_by_commune 
                   (annee, programme, categorie_juridique, code_commune, montant_cp);"""
    op.execute(index_m_view_cp)

    m_view_montant_par_niveau_annee_programme = """CREATE MATERIALIZED VIEW montant_par_niveau_bop_annee_type AS 
              SELECT 
                SUM(montant_cp) as montant_cp,
                (SELECT SUM(fce.montant_ae) FROM financial_ae_summary_by_commune fce WHERE fce.programme = fcp.programme
                and fce.annee = fcp.annee AND fce.code_commune = fcp.code_commune and fce.categorie_juridique = fcp.categorie_juridique) as montant_ae,
                'commune' as niveau,
                annee,
                programme,
                code_commune as code,
                categorie_juridique as type
            FROM financial_cp_summary_by_commune fcp
            GROUP BY annee, programme, categorie_juridique, code_commune
            UNION
             SELECT 
                SUM(montant_cp) as montant_cp,
                (SELECT SUM(fce.montant_ae) FROM financial_ae_summary_by_commune fce WHERE fce.programme = fcp.programme
                and fce.annee = fcp.annee AND fce.code_departement = fcp.code_departement and fce.categorie_juridique = fcp.categorie_juridique) as montant_ae,
                'departement' as niveau,
                annee,
                programme,
                code_departement as code,
                categorie_juridique as type
            FROM financial_cp_summary_by_commune fcp
            GROUP BY annee, programme, categorie_juridique, code_departement
            UNION
             SELECT 
                SUM(montant_cp) as montant_cp,
                (SELECT SUM(fce.montant_ae) FROM financial_ae_summary_by_commune fce WHERE fce.programme = fcp.programme
                and fce.annee = fcp.annee AND fce.code_crte = fcp.code_crte and fce.categorie_juridique = fcp.categorie_juridique) as montant_ae,
                'crte' as niveau,
                annee,
                programme,
                code_crte as code,
                categorie_juridique as type
            FROM financial_cp_summary_by_commune fcp
            GROUP BY annee, programme, categorie_juridique, code_crte
            UNION
             SELECT 
                SUM(montant_cp) as montant_cp,
               (SELECT SUM(fce.montant_ae) FROM financial_ae_summary_by_commune fce WHERE fce.programme = fcp.programme
                and fce.annee = fcp.annee AND fce.code_epci = fcp.code_epci and fce.categorie_juridique = fcp.categorie_juridique) as montant_ae,
                'epci' as niveau,
                annee,
                programme,
                code_epci as code,
                categorie_juridique as type
            FROM financial_cp_summary_by_commune fcp
            GROUP BY annee, programme, categorie_juridique, code_epci;"""

    op.execute(m_view_montant_par_niveau_annee_programme)
    # ### end Alembic commands ###


def downgrade():
    op.execute("DROP MATERIALIZED  VIEW financial_cp_summary_by_commune")
    op.execute("DROP MATERIALIZED  VIEW financial_ae_summary_by_commune")
    op.execute("DROP MATERIALIZED  VIEW montant_par_niveau_bop_annee_type")



def _drop_old_view():
    op.execute("DROP VIEW IF EXISTS public.montant_par_niveau_bop_annee_type")
    op.execute("DROP VIEW IF EXISTS public.montant_par_commune_type")
    op.execute("DROP VIEW IF EXISTS public.montant_par_commune_type_theme")
    op.execute("DROP VIEW IF EXISTS public.montant_par_commune")

