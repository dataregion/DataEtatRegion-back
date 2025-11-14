from typing import List
from models.entities.common.Tags import Tags
from models.entities.financial.query import AbstractFlattenFinancialLines
from sqlalchemy.orm import relationship, Mapped


class FlattenFinancialLines(AbstractFlattenFinancialLines):
    """
    Table correspondant à la vue à plat des lignes financières.
    """

    __tablename__ = "flatten_financial_lines"
    __table_args__ = {"info": {"skip_autogenerate": True}}


class EnrichedFlattenFinancialLines(FlattenFinancialLines):
    """
    Vue des données financières à plat enrichies avec
    des données associées à l'application (ie: les tags).
    """

    tags: Mapped[List[Tags]] = relationship(
        "Tags",
        uselist=True,
        lazy="joined",
        secondary="tag_association",
        primaryjoin=(
            "or_("
            "and_(EnrichedFlattenFinancialLines.id==TagAssociation.financial_ae, EnrichedFlattenFinancialLines.source=='FINANCIAL_DATA_AE'),"
            "and_(EnrichedFlattenFinancialLines.id==TagAssociation.financial_cp, EnrichedFlattenFinancialLines.source=='FINANCIAL_DATA_CP'),"
            "and_(EnrichedFlattenFinancialLines.id==TagAssociation.ademe, EnrichedFlattenFinancialLines.source=='ADEME'),"
            ")"
        ),
        viewonly=True,
    )
