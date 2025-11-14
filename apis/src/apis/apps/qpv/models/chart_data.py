from typing import List
from pydantic import BaseModel


class ChartData(BaseModel):
    labels: List[str]
    values: List[float]
