"""empty message

Revision ID: 695c5c3b7741
Revises: 20230519_montant_ae
Create Date: 2023-06-07 17:45:16.653781

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20230607_ademe"
down_revision = "20230519_montant_ae"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "ademe",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("date_convention", sa.Date(), nullable=True),
        sa.Column("reference_decision", sa.String(length=255), nullable=False),
        sa.Column("objet", sa.String(length=255), nullable=True),
        sa.Column("montant", sa.Float(), nullable=True),
        sa.Column("nature", sa.String(length=255), nullable=True),
        sa.Column("conditions_versement", sa.String(length=255), nullable=True),
        sa.Column("dates_periode_versement", sa.String(length=255), nullable=True),
        sa.Column("notification_ue", sa.Boolean(), default=False, nullable=True),
        sa.Column("pourcentage_subvention", sa.Float(), nullable=True),
        sa.Column("siret_beneficiaire", sa.String(), nullable=True),
        sa.Column("siret_attribuant", sa.String(), nullable=True),
        sa.Column("location_lat", sa.Float(), nullable=True),
        sa.Column("location_lon", sa.Float(), nullable=True),
        sa.Column("departement", sa.String(length=5), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=True),
        sa.Column("updated_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(
            ["siret_attribuant"],
            ["ref_siret.code"],
        ),
        sa.ForeignKeyConstraint(
            ["siret_beneficiaire"],
            ["ref_siret.code"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    with op.batch_alter_table("ref_siret", schema=None) as batch_op:
        batch_op.add_column(sa.Column("naf", postgresql.JSONB(astext_type=sa.Text()), nullable=True))

    # supression value FINANCIAL_DATA
    op.execute("ALTER TYPE datatype RENAME TO datatype_old")
    op.execute(
        "CREATE TYPE datatype AS ENUM('FINANCIAL_DATA_AE', 'FINANCIAL_DATA_CP', 'FRANCE_RELANCE','REFERENTIEL','ADEME')"
    )

    op.execute(
        "ALTER TABLE audit.audit_update_data ALTER COLUMN data_type TYPE datatype USING data_type::text::datatype;"
    )
    op.execute("DROP TYPE datatype_old")

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    with op.batch_alter_table("ref_siret", schema=None) as batch_op:
        batch_op.drop_column("naf")

    op.drop_table("ademe")
    # ### end Alembic commands ###
