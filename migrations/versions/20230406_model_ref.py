"""empty message

Revision ID: a4e1210b7130
Revises: 20230316_annee_chorus
Create Date: 2023-03-17 17:00:22.038372

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20230406_model_ref"
down_revision = "20230316_annee_chorus"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    _update_code_programmation()
    _update_code_centre_couts()

    _upgrade_tables()
    _add_columns_audit()

    # Audit
    op.execute("CREATE SCHEMA if not exists audit")

    op.create_table(
        "audit_update_data",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("username", sa.String(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column(
            "data_type", sa.Enum("FINANCIAL_DATA", "FRANCE_RELANCE", "REFERENTIEL", name="datatype"), nullable=False
        ),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        schema="audit",
    )

    # ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###

    _drop_columns_audit()
    op.drop_column("ref_localisation_interministerielle", "site")
    op.drop_column("ref_localisation_interministerielle", "commune")
    op.drop_column("ref_localisation_interministerielle", "code_departement")
    op.drop_column("ref_localisation_interministerielle", "niveau")
    op.drop_column("ref_localisation_interministerielle", "code_parent")

    op.drop_column("ref_groupe_marchandise", "label_pce")
    op.drop_column("ref_groupe_marchandise", "code_pce")
    op.drop_column("ref_groupe_marchandise", "domaine")
    op.drop_column("ref_groupe_marchandise", "segment")

    op.drop_column("ref_code_programme", "code_ministere")
    op.drop_column("ref_centre_couts", "ville")
    op.drop_column("ref_centre_couts", "code_postal")

    op.create_table(
        "ref_compte_general",
        sa.Column("id", sa.INTEGER(), autoincrement=True, nullable=False),
        sa.Column("code", sa.VARCHAR(), autoincrement=False, nullable=False),
        sa.Column("label", sa.VARCHAR(), autoincrement=False, nullable=True),
        sa.Column("description", sa.TEXT(), autoincrement=False, nullable=True),
        sa.PrimaryKeyConstraint("id", name="ref_compte_general_pkey"),
        sa.UniqueConstraint("code", name="ref_compte_general_code_key"),
    )

    op.add_column("data_chorus", sa.Column("compte_general", sa.VARCHAR(), autoincrement=False, nullable=True))
    op.create_foreign_key(
        "data_chorus_compte_general_fkey", "data_chorus", "ref_compte_general", ["compte_general"], ["code"]
    )

    op.drop_table("ref_ministere")

    op.add_column(
        "ref_siret", sa.Column("longitude", sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True)
    )
    op.add_column(
        "ref_siret", sa.Column("latitude", sa.DOUBLE_PRECISION(precision=53), autoincrement=False, nullable=True)
    )

    op.drop_table("audit_update_data", schema="audit")

    sql_drop_type = "DROP TYPE datatype"
    op.execute(sql_drop_type)

    # ### end Alembic commands ###


def _update_code_programmation():
    """
    Update les valeurs de la table ref_programmation
    (suppression du prefix BGOO/)"
    :return:
    """
    sql_update_code = "INSERT INTO ref_programmation (code,label) (SELECT SUBSTRING(code,6), label FROM ref_programmation WHERE code LIKE 'BG00/%')"
    sql_update_chorus = "UPDATE data_chorus SET referentiel_programmation = SUBSTRING(referentiel_programmation,6) WHERE referentiel_programmation LIKE 'BG00/%'"
    sql_delete_old_code = "DELETE FROM ref_programmation WHERE code LIKE 'BG00/%'"

    op.execute(sql_update_code)
    op.execute(sql_update_chorus)
    op.execute(sql_delete_old_code)


def _update_code_centre_couts():
    """
    Update les valeurs de la table ref_centre_couts
    (suppression du prefix BGOO/)"
    :return:
    """
    sql_update_code = "INSERT INTO ref_centre_couts (code,label) (SELECT SUBSTRING(code,6), label FROM ref_centre_couts WHERE code LIKE 'BG00/%')"
    sql_update_chorus = (
        "UPDATE data_chorus SET centre_couts = SUBSTRING(centre_couts,6) WHERE centre_couts LIKE 'BG00/%'"
    )
    sql_delete_old_code = "DELETE FROM ref_centre_couts WHERE code LIKE 'BG00/%'"

    op.execute(sql_update_code)
    op.execute(sql_update_chorus)
    op.execute(sql_delete_old_code)


def _add_columns_audit():
    op.add_column("ref_categorie_juridique", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_categorie_juridique", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("ref_centre_couts", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_centre_couts", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("ref_code_programme", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_code_programme", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("ref_commune", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_commune", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("ref_domaine_fonctionnel", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_domaine_fonctionnel", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("ref_fournisseur_titulaire", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_fournisseur_titulaire", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("ref_groupe_marchandise", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_groupe_marchandise", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("ref_localisation_interministerielle", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_localisation_interministerielle", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("ref_ministere", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_ministere", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("ref_programmation", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_programmation", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("ref_siret", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_siret", sa.Column("updated_at", sa.DateTime(), nullable=True))
    op.add_column("ref_theme", sa.Column("created_at", sa.DateTime(), nullable=True))
    op.add_column("ref_theme", sa.Column("updated_at", sa.DateTime(), nullable=True))


def _upgrade_tables():
    # REF MINISTERE
    op.create_table(
        "ref_ministere",
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("sigle_ministere", sa.String(), nullable=True),
        sa.Column("label", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.PrimaryKeyConstraint("code"),
    )
    # DROP Compte generale
    op.drop_constraint("data_chorus_compte_general_fkey", "data_chorus", type_="foreignkey")
    op.drop_column("data_chorus", "compte_general")
    op.drop_table("ref_compte_general")

    # UPDATE CENTRE COUTS
    op.add_column("ref_centre_couts", sa.Column("code_postal", sa.String(), nullable=True))
    op.add_column("ref_centre_couts", sa.Column("ville", sa.String(), nullable=True))
    op.add_column("ref_code_programme", sa.Column("code_ministere", sa.String(), nullable=True))

    # ADD FK MINISTERE TO CODE PROGRAMME
    op.create_foreign_key(
        "ref_code_programme_ref_ministere_fkey", "ref_code_programme", "ref_ministere", ["code_ministere"], ["code"]
    )

    # UPDATE groupe marchandise
    op.add_column("ref_groupe_marchandise", sa.Column("code_pce", sa.String(), nullable=True))
    op.add_column("ref_groupe_marchandise", sa.Column("label_pce", sa.String(), nullable=True))
    op.add_column("ref_groupe_marchandise", sa.Column("domaine", sa.String(), nullable=True))
    op.add_column("ref_groupe_marchandise", sa.Column("segment", sa.String(), nullable=True))

    # UPDATE localisation interministerielle
    op.add_column("ref_localisation_interministerielle", sa.Column("code_departement", sa.String(), nullable=True))
    op.add_column("ref_localisation_interministerielle", sa.Column("commune", sa.String(), nullable=True))
    op.add_column("ref_localisation_interministerielle", sa.Column("site", sa.String(), nullable=True))
    op.add_column("ref_localisation_interministerielle", sa.Column("niveau", sa.String(), nullable=True))
    op.add_column("ref_localisation_interministerielle", sa.Column("code_parent", sa.String(), nullable=True))

    # DROP Colonnes longitude/latitude pour siret
    op.drop_column("ref_siret", "latitude")
    op.drop_column("ref_siret", "longitude")


def _drop_columns_audit():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column("ref_theme", "updated_at")
    op.drop_column("ref_theme", "created_at")
    op.drop_column("ref_siret", "updated_at")
    op.drop_column("ref_siret", "created_at")
    op.drop_column("ref_programmation", "updated_at")
    op.drop_column("ref_programmation", "created_at")
    op.drop_column("ref_ministere", "updated_at")
    op.drop_column("ref_ministere", "created_at")
    op.drop_column("ref_localisation_interministerielle", "updated_at")
    op.drop_column("ref_localisation_interministerielle", "created_at")
    op.drop_column("ref_groupe_marchandise", "updated_at")
    op.drop_column("ref_groupe_marchandise", "created_at")
    op.drop_column("ref_fournisseur_titulaire", "updated_at")
    op.drop_column("ref_fournisseur_titulaire", "created_at")
    op.drop_column("ref_domaine_fonctionnel", "updated_at")
    op.drop_column("ref_domaine_fonctionnel", "created_at")
    op.drop_column("ref_commune", "updated_at")
    op.drop_column("ref_commune", "created_at")
    op.drop_column("ref_code_programme", "updated_at")
    op.drop_column("ref_code_programme", "created_at")
    op.drop_column("ref_centre_couts", "updated_at")
    op.drop_column("ref_centre_couts", "created_at")
    op.drop_column("ref_categorie_juridique", "updated_at")
    op.drop_column("ref_categorie_juridique", "created_at")
