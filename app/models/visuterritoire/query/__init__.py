from app import db, ma
from sqlalchemy import Column, Integer, String, Date, Float, Boolean


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

    source = Column(String, nullable=True, primary_key=True)

    programme = Column(String, nullable=True, primary_key=True)
    code = Column(String, nullable=True, primary_key=True)
    type = Column(String, nullable=True, primary_key=True)


class MontantParNiveauBopAnneeTypeSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = MontantParNiveauBopAnneeType


class France2030(db.Model):
    """
    Table correspondant à la vue visuterritoire correspondante
    """

    #
    # XXX: C'est un value object
    # donc pas de primary key -> toutes les colonnes sont PK
    #

    __tablename__ = "v_france_2030"

    date_dpm = Column(Date, nullable=True, primary_key=True)
    operateur = Column(String, nullable=True, primary_key=True)
    procedure = Column(String, nullable=True, primary_key=True)
    nom_projet = Column(String, nullable=True, primary_key=True)
    typologie = Column(String, nullable=True, primary_key=True)
    nom_strategie = Column(String, nullable=True, primary_key=True)
    montant_subvention = Column(Float, nullable=True, primary_key=True)
    montant_avance_remboursable = Column(Float, nullable=True, primary_key=True)
    montant_aide = Column(Float, nullable=True, primary_key=True)
    siret = Column(String, nullable=True, primary_key=True)
    code_nomenclature = Column(String, nullable=True, primary_key=True)
    annee = Column(Integer, nullable=True, primary_key=True)
    numero = Column(Integer, nullable=True, primary_key=True)
    mot = Column(String, nullable=True, primary_key=True)
    phrase = Column(String, nullable=True, primary_key=True)
    categorie_juridique = Column(String, nullable=True)
    code_commune = Column(String, nullable=True)
    nom_beneficiaire = Column(String, nullable=True)
    adresse = Column(String, nullable=True)
    code_qpv = Column(String, nullable=True)
    label_commune = Column(String, nullable=True)
    code_crte = Column(String, nullable=True)
    label_crte = Column(String, nullable=True)
    code_region = Column(String, nullable=True)
    label_region = Column(String, nullable=True)
    code_epci = Column(String, nullable=True)
    label_epci = Column(String, nullable=True)
    code_departement = Column(String, nullable=True)
    label_departement = Column(String, nullable=True)
    is_pvd = Column(Boolean, nullable=True)
    date_pvd = Column(Date, nullable=True)
    is_acv = Column(Boolean, nullable=True)
    date_acv = Column(Date, nullable=True)
    code_arrondissement = Column(String, nullable=True)
    label_arrondissement = Column(String, nullable=True)
    categorie_typologie = Column(String, nullable=True)
    code_iso_region = Column(String, nullable=True)


class France2030Schema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = France2030
