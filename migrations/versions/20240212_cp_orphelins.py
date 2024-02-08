"""

Revision ID: 20240212_cp_orphelins
Revises: 20240122_france2030
Create Date: 2024-02-01 16:46:01.020809

"""
from pathlib import Path
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "20240212_cp_orphelins"
down_revision = "20240122_france2030"
branch_labels = None
depends_on = None

_data_folder = Path(__file__).resolve().parent / __name__

new_views = ["flatten_orphan_cp", "_flatten_financial_lines"]
views_to_restore_on_downgrade = ["_flatten_financial_lines"]
views_to_delete_on_downgrade = ["flatten_orphan_cp"]
materialized_views_to_refresh = ["flatten_financial_lines"]


def upgrade():
    _upgrade_tags()
    _upgrade_tags_association()

    for view in new_views:
        print(f"Création de la vue {view}")
        op.execute(_new_filecontent(f"{view}.sql"))

    _refresh_materialized_views()

    # Delete cascade entre AE et montant
    with op.batch_alter_table("montant_financial_ae", schema=None) as batch_op:
        batch_op.drop_constraint("montant_financial_ae_id_financial_ae_fkey", type_="foreignkey")
        batch_op.create_foreign_key("montant_financial_ae_id_financial_ae_fkey", "financial_ae", ["id_financial_ae"], ["id"], ondelete="cascade")


def downgrade():
    for view in views_to_restore_on_downgrade:
        print(f"Restaure l'ancienne version de {view}")
        op.execute(_old_filecontent(f"{view}.sql"))

    for view in views_to_delete_on_downgrade:
        print(f"Drop de la vue {view}")
        op.execute(f"DROP VIEW IF EXISTS public.{view}")

    _downgrade_tags_association()
    _downgrade_tags()

    _refresh_materialized_views()

    # Pas de delete cascade entre AE et montant
    with op.batch_alter_table("montant_financial_ae", schema=None) as batch_op:
        batch_op.drop_constraint("montant_financial_ae_id_financial_ae_fkey", type_="foreignkey")
        batch_op.create_foreign_key("montant_financial_ae_id_financial_ae_fkey", "financial_ae", ["id_financial_ae"], ["id"])


def _refresh_materialized_views():
    for view in materialized_views_to_refresh:
        print(f"refresh materialized view {view}")
        op.execute(f"REFRESH MATERIALIZED VIEW {view}")


def _upgrade_tags_association():
    print("Upgrade structure of tag association")
    with op.batch_alter_table("tag_association", schema=None) as batch_op:
        batch_op.add_column(sa.Column("financial_cp", sa.Integer(), nullable=True))

        batch_op.create_index(batch_op.f("ix_tag_association_financial_cp"), ["financial_cp"], unique=False)

        batch_op.drop_constraint("tag_association_financial_ae_fkey", type_="foreignkey")
        batch_op.drop_constraint("tag_association_ademe_fkey", type_="foreignkey")

        batch_op.create_foreign_key("tag_association_ademe_fkey", "ademe", ["ademe"], ["id"], ondelete="cascade")
        batch_op.create_foreign_key(
            "tag_association_financial_ae_fkey", "financial_ae", ["financial_ae"], ["id"], ondelete="cascade"
        )
        batch_op.create_foreign_key(
            "tag_association_financial_cp_fkey", "financial_cp", ["financial_cp"], ["id"], ondelete="cascade"
        )

    op.drop_constraint("line_fks_xor", table_name="tag_association")
    op.create_check_constraint(
        "line_fks_xor", table_name="tag_association", condition="num_nonnulls(ademe, financial_ae, financial_cp) = 1"
    )


def _downgrade_tags_association():
    print("Downgrade structure of tag association")

    with op.batch_alter_table("tag_association", schema=None) as batch_op:
        print("Suppression des associations concernant les CP")
        stmt = """
        delete from tag_association ta
        where ta.financial_cp is not NULL;
        """
        op.execute(stmt)

        batch_op.drop_constraint("line_fks_xor")
        batch_op.create_check_constraint("line_fks_xor", condition="num_nonnulls(ademe, financial_ae) = 1")

        batch_op.drop_column("financial_cp")

        batch_op.drop_constraint("tag_association_ademe_fkey", type_="foreignkey")
        batch_op.drop_constraint("tag_association_financial_ae_fkey", type_="foreignkey")

        batch_op.create_foreign_key("tag_association_ademe_fkey", "ademe", ["ademe"], ["id"])
        batch_op.create_foreign_key("tag_association_financial_ae_fkey", "financial_ae", ["financial_ae"], ["id"])


def _upgrade_tags():
    print("Ajout du tag cp-orphelin")
    display_name = "Crédit de paiement orphelin"
    description = f"La ligne est taguée « {display_name} » est un crédit de paiement sans engagement attaché."

    stmt = f"""
    INSERT INTO tags
    ("type", value, description, enable_rules_auto, created_at, updated_at, display_name)
    VALUES('cp-orphelin', NULL, '{description}', true, NULL, NULL, '{display_name}');
    """
    op.execute(stmt)


def _downgrade_tags():
    print("Delete du tag cp-orphelin")
    stmt = """
    DELETE FROM tags
    WHERE type = 'cp-orphelin';
    """
    op.execute(stmt)


def _new_filecontent(name: str):
    """Get file content from ./`modulename`/new/name"""
    p = _data_folder / "new" / name
    with p.open("r") as f:
        view_str = f.read()
    return view_str


def _old_filecontent(name: str):
    """Get file content from ./`modulename`/old/name"""
    p = _data_folder / "old" / name
    with p.open("r") as f:
        view_str = f.read()
    return view_str
