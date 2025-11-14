from pydantic import BaseModel


class QpvData(BaseModel):
    qpv: str = ""
    montant: float = 0.0


class MapData(BaseModel):
    data: list[QpvData] = None
