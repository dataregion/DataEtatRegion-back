"""empty message

Revision ID: 20230208_ref_region
Revises: 20230201_audit_preference
Create Date: 2023-02-08 13:01:22.259010

"""
import logging
import pandas
from alembic import op
import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy import Column, String


# revision identifiers, used by Alembic.
revision = "20230208_pref_and_region"
down_revision = "20230113_preference"
branch_labels = None
depends_on = None

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class _Base(orm.DeclarativeBase):
    pass


class _Region(_Base):
    __tablename__ = "ref_region"
    id = Column(sa.Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    label = Column(String)


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###

    #
    # Audit preference
    #

    query_column_date_creation = (
        "ALTER TABLE settings.preference_users ADD COLUMN date_creation timestamptz DEFAULT CURRENT_TIMESTAMP"
    )
    query_column_dernier_acces = (
        "ALTER TABLE settings.preference_users ADD COLUMN dernier_acces timestamptz DEFAULT NULL"
    )
    query_column_nombre_utilisation = (
        "ALTER TABLE settings.preference_users ADD COLUMN nombre_utilisation INTEGER DEFAULT 0"
    )
    query_column_email_send = "ALTER TABLE settings.share_preference ADD COLUMN email_send BOOLEAN DEFAULT False"
    query_column_application = (
        "ALTER TABLE settings.preference_users ADD COLUMN application_host VARCHAR  NOT NULL DEFAULT ''"
    )

    op.execute(query_column_date_creation)
    op.execute(query_column_dernier_acces)
    op.execute(query_column_nombre_utilisation)
    op.execute(query_column_email_send)
    op.execute(query_column_application)

    #
    # Ref region
    #
    op.create_table(
        "ref_region",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("code", sa.String(), nullable=False),
        sa.Column("label", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("code"),
    )

    _insert_ref()

    op.add_column("data_chorus", sa.Column("source_region", sa.String(), nullable=True))
    op.create_foreign_key(None, "data_chorus", "ref_region", ["source_region"], ["code"])
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    #
    # Ref region
    #
    op.drop_constraint("data_chorus_source_region_fkey", "data_chorus", type_="foreignkey")
    op.drop_column("data_chorus", "source_region")
    op.drop_table("ref_region")

    #
    # Audit preferences
    #
    query_column_date_creation = "ALTER TABLE settings.preference_users DROP COLUMN date_creation "
    query_column_dernier_acces = "ALTER TABLE settings.preference_users DROP COLUMN dernier_acces "
    query_column_nombre_utilisation = "ALTER TABLE settings.preference_users DROP COLUMN nombre_utilisation "
    query_column_email_send = "ALTER TABLE settings.share_preference DROP COLUMN email_send "

    query_column_application = "ALTER TABLE settings.preference_users DROP COLUMN application_host"

    op.execute(query_column_date_creation)
    op.execute(query_column_dernier_acces)
    op.execute(query_column_nombre_utilisation)
    op.execute(query_column_email_send)
    op.execute(query_column_application)
    # ### end Alembic commands ###


def _insert_ref():
    file_regions = f"migrations.old/data/{revision}/ref_regions.csv"

    session = orm.Session(bind=op.get_bind())
    data_frame = pandas.read_csv(
        file_regions,
        usecols=["REG", "LIBELLE"],
        sep=",",
        dtype=str,
    )
    try:
        for index, region in data_frame.iterrows():
            code_insee = str(region["REG"])
            libelle = str(region["LIBELLE"])

            region = session.query(_Region).filter_by(**{"code": code_insee}).one_or_none()

            if region is None:
                region = _Region(code=code_insee, label=libelle)
                session.add(region)
                session.commit()
            else:
                logger.info(f"Ignore ligne {index}" ", code insee: {region['REG']}, label: {region['LIBELLE']}")
    except Exception as e:
        logger.exception(e)
        raise
