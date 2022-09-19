"""empty message

Revision ID: e1909379b371
Revises: 
Create Date: 2022-09-19 10:11:19.917141

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e1909379b371'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('ref_centre_couts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('ref_code_programme',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('ref_compte_general',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('ref_domaine_fonctionnel',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('ref_fournisseur_titulaire',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('ref_groupe_marchandise',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('ref_localisation_interministerielle',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('ref_programmation',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('code', sa.String(), nullable=False),
    sa.Column('label', sa.String(), nullable=True),
    sa.Column('description', sa.Text(), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('code')
    )
    op.create_table('siret',
    sa.Column('siret', sa.Integer(), nullable=False),
    sa.Column('type_etablissement', sa.String(), nullable=True),
    sa.Column('code_commune', sa.String(), nullable=True),
    sa.Column('departement', sa.String(), nullable=True),
    sa.Column('denomination', sa.String(), nullable=True),
    sa.Column('adresse', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('siret')
    )
    op.create_table('data_chorus',
    sa.Column('n_ej', sa.String(), nullable=False),
    sa.Column('n_poste_ej', sa.Integer(), nullable=False),
    sa.Column('programme', sa.String(), nullable=False),
    sa.Column('domaine_fonctionnel', sa.String(), nullable=False),
    sa.Column('centre_couts', sa.String(), nullable=False),
    sa.Column('referentiel_programmation', sa.String(), nullable=False),
    sa.Column('localisation_interministerielle', sa.String(), nullable=False),
    sa.Column('groupe_marchandise', sa.String(), nullable=False),
    sa.Column('compte_general', sa.String(), nullable=False),
    sa.Column('fournisseur_titulaire', sa.String(), nullable=False),
    sa.Column('siret', sa.Integer(), nullable=False),
    sa.Column('date_modification_ej', sa.DateTime(), nullable=False),
    sa.Column('compte_budgetaire', sa.String(length=255), nullable=False),
    sa.Column('contrat_etat_region', sa.String(length=255), nullable=True),
    sa.Column('montant', sa.Float(), nullable=True),
    sa.ForeignKeyConstraint(['centre_couts'], ['ref_centre_couts.code'], ),
    sa.ForeignKeyConstraint(['compte_general'], ['ref_compte_general.code'], ),
    sa.ForeignKeyConstraint(['domaine_fonctionnel'], ['ref_domaine_fonctionnel.code'], ),
    sa.ForeignKeyConstraint(['fournisseur_titulaire'], ['ref_fournisseur_titulaire.code'], ),
    sa.ForeignKeyConstraint(['groupe_marchandise'], ['ref_groupe_marchandise.code'], ),
    sa.ForeignKeyConstraint(['localisation_interministerielle'], ['ref_localisation_interministerielle.code'], ),
    sa.ForeignKeyConstraint(['programme'], ['ref_code_programme.code'], ),
    sa.ForeignKeyConstraint(['referentiel_programmation'], ['ref_programmation.code'], ),
    sa.ForeignKeyConstraint(['siret'], ['siret.siret'], ),
    sa.PrimaryKeyConstraint('n_ej', 'n_poste_ej')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('data_chorus')
    op.drop_table('siret')
    op.drop_table('ref_programmation')
    op.drop_table('ref_localisation_interministerielle')
    op.drop_table('ref_groupe_marchandise')
    op.drop_table('ref_fournisseur_titulaire')
    op.drop_table('ref_domaine_fonctionnel')
    op.drop_table('ref_compte_general')
    op.drop_table('ref_code_programme')
    op.drop_table('ref_centre_couts')
    # ### end Alembic commands ###
