from models.entities.financial.query import AbstractFlattenFinancialLines


class FlattenFinancialLinesDataQPV(AbstractFlattenFinancialLines):
    """
    Table correspondant à la vue à plat des lignes financières filtrées pour Data QPV.
    """
    __tablename__ = "flatten_financial_lines_data_qpv"
    __table_args__ = {"info": {"skip_autogenerate": True}}
