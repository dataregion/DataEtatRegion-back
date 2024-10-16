from dataclasses import dataclass

from app.models.utils import _AddMarshmallowSchema


@dataclass
class AffichageDossier(metaclass=_AddMarshmallowSchema):
    nomDemarche: str
    numeroDossier: int
    nomProjet: str
    descriptionProjet: str
    categorieProjet: str
    coutProjet: str
    montantDemande: str
    montantAccorde: str
    dateFinProjet: str
    contact: str
