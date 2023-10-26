"""Assainit le nom de tags actuels

Revision ID: 20231026_fix_tags_case
Revises: edc5f93432df
Create Date: 2023-10-26 09:51:22.694107

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "20231026_fix_tags_case"
down_revision = "edc5f93432df"
branch_labels = None
depends_on = None

correspondances = [
    ["Fond vert", "fonds-vert"],
    ["CPER", "cper"],
    ["DETR", "dter"],
    ["Relance", "relance"],
]


def upgrade():
    for correspondance in correspondances:
        original, replacement = correspondance

        op.execute(
            f"""
            UPDATE tags SET type = REPLACE(type, '{original}', '{replacement}');
            """
        )

    # region Constraint

    #### all lowercas
    op.execute(
        """
        ALTER TABLE tags
        ADD CONSTRAINT tags_type_lowercase
        CHECK (type = lower(type));
        """
    )
    op.execute(
        """
        ALTER TABLE tags
        ADD CONSTRAINT tags_value_lowercase
        CHECK (value = lower(value));
        """
    )

    #### no space
    op.execute(
        """
        ALTER TABLE tags
        ADD CONSTRAINT tags_type_nospace
        CHECK (type NOT LIKE '% %');
        """
    )
    op.execute(
        """
        ALTER TABLE tags
        ADD CONSTRAINT tags_value_nospace
        CHECK (value NOT LIKE '% %');
        """
    )

    # endregion


def downgrade():
    # region Constraint

    #### all lowercas
    op.execute(
        """
        ALTER TABLE tags
        DROP CONSTRAINT tags_type_lowercase
        """
    )
    op.execute(
        """
        ALTER TABLE tags
        DROP CONSTRAINT tags_value_lowercase
        """
    )

    #### no space
    op.execute(
        """
        ALTER TABLE tags
        DROP CONSTRAINT tags_type_nospace
        """
    )
    op.execute(
        """
        ALTER TABLE tags
        DROP CONSTRAINT tags_value_nospace
        """
    )

    # endregion

    for correspondance in correspondances:
        original, replacement = correspondance

        op.execute(
            f"""
            UPDATE tags SET type = REPLACE(type, '{replacement}', '{original}');
            """
        )
