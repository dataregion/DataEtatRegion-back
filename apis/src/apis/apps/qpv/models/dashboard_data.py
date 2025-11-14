from apis.apps.qpv.models.chart_data import ChartData
from pydantic import BaseModel


class DashboardData(BaseModel):
    total_financements: float = 0.0
    total_actions: float = 0.0
    total_porteurs: float = 0.0
    pie_chart_themes: ChartData = None
    pie_chart_types_porteurs: ChartData = None
    bar_chart_financeurs: ChartData = None
    line_chart_annees: ChartData = None
