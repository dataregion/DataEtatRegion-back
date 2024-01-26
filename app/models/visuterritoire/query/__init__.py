from app import db, ma
from sqlalchemy import Column, Integer, String


class MontantParNiveauBopAnneeType(db.Model):
    """
    Table correspondant à la vue visuterritoire correspondante
    """

    #
    # XXX: C'est un value object
    # donc pas de primary key -> toutes les colonnes sont PK
    #

    __tablename__ = "montant_par_niveau_bop_annee_type"

    montant_ae = Column(Integer, nullable=True, primary_key=True)
    montant_cp = Column(Integer, nullable=True, primary_key=True)

    niveau = Column(String, nullable=True, primary_key=True)

    annee = Column(Integer, nullable=True, primary_key=True)

    programme = Column(String, nullable=True, primary_key=True)
    code = Column(String, nullable=True, primary_key=True)
    type = Column(String, nullable=True, primary_key=True)


class MontantParNiveauBopAnneeTypeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = MontantParNiveauBopAnneeType
