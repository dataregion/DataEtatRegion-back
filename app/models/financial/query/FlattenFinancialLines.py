from sqlalchemy import Column, Float, Integer, String, DateTime
from sqlalchemy.orm import relationship, Mapped

from marshmallow import fields

from app import db, ma
from app.models.enums.DataType import DataTypeField
from app.models.tags.Tags import Tags, TagsSchema


class FlattenFinancialLines(db.Model):
    """
    Table correspondant à la vue à plat des lignes financières.
    """

    __tablename__ = "flatten_financial_lines"

    source = Column(String, nullable=False)
    """Source de la ligne (ademe, chorus etc...). C'est l'enum DataType qui est pris ici."""

    id = Column(Integer, primary_key=True, nullable=False)

    n_ej = Column(String)
    n_poste_ej = Column(Integer)

    annee = Column(Integer)
    contrat_etat_region = Column(String)
    compte_budgetaire = Column(String)

    montant_ae = Column(Float)
    montant_cp = Column(Float)

    dateDeDernierPaiement = Column(DateTime)
    dateDeCreation = Column(DateTime)

    domaineFonctionnel_code = Column(String)
    domaineFonctionnel_label = Column(String)

    referentielProgrammation_code = Column(String)
    referentielProgrammation_label = Column(String)

    groupeMarchandise_code = Column(String)
    groupeMarchandise_label = Column(String)

    programme_code = Column(String)
    programme_label = Column(String)
    programme_theme = Column(String)

    beneficiaire_code = Column(String)
    beneficiaire_denomination = Column(String)
    beneficiaire_categorieJuridique_type = Column(String)
    beneficiaire_qpv_code = Column(String)
    beneficiaire_qpv_label = Column(String)
    beneficiaire_commune_code = Column(String)
    beneficiaire_commune_label = Column(String)
    beneficiaire_commune_codeRegion = Column(String)
    beneficiaire_commune_labelRegion = Column(String)
    beneficiaire_commune_codeDepartement = Column(String)
    beneficiaire_commune_labelDepartement = Column(String)
    beneficiaire_commune_codeEpci = Column(String)
    beneficiaire_commune_labelEpci = Column(String)
    beneficiaire_commune_codeCrte = Column(String)
    beneficiaire_commune_labelCrte = Column(String)
    beneficiaire_commune_arrondissement_code = Column(String)
    beneficiaire_commune_arrondissement_label = Column(String)

    localisationInterministerielle_code = Column(String)
    localisationInterministerielle_label = Column(String)
    localisationInterministerielle_codeDepartement = Column(String)
    localisationInterministerielle_commune_code = Column(String)
    localisationInterministerielle_commune_label = Column(String)
    localisationInterministerielle_commune_codeRegion = Column(String)
    localisationInterministerielle_commune_labelRegion = Column(String)
    localisationInterministerielle_commune_codeDepartement = Column(String)
    localisationInterministerielle_commune_labelDepartement = Column(String)
    localisationInterministerielle_commune_codeEpci = Column(String)
    localisationInterministerielle_commune_labelEpci = Column(String)
    localisationInterministerielle_commune_codeCrte = Column(String)
    localisationInterministerielle_commune_labelCrte = Column(String)
    localisationInterministerielle_commune_arrondissement_code = Column(String)
    localisationInterministerielle_commune_arrondissement_label = Column(String)

    source_region = Column(String)

    updated_at = Column(DateTime)
    created_at = Column(DateTime)


class EnrichedFlattenFinancialLines(FlattenFinancialLines):
    """
    Vue des données financières à plat enrichies avec
    des données associées à l'application (ie: les tags).
    """

    tags: Mapped[Tags] = relationship(
        "Tags",
        uselist=True,
        lazy="joined",
        secondary="tag_association",
        primaryjoin=(
            "or_("
            "and_(EnrichedFlattenFinancialLines.id==TagAssociation.financial_ae, EnrichedFlattenFinancialLines.source=='FINANCIAL_DATA_AE'),"
            "and_(EnrichedFlattenFinancialLines.id==TagAssociation.ademe, EnrichedFlattenFinancialLines.source=='ADEME'),"
            ")"
        ),
        viewonly=True,
    )


class EnrichedFlattenFinancialLinesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = EnrichedFlattenFinancialLines

    source = DataTypeField()

    tags = fields.List(fields.Nested(TagsSchema))
