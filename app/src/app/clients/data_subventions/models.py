from dataclasses import dataclass

from app.models.utils import _InstrumentForFlaskRestx


@dataclass
class RepresentantLegal(metaclass=_InstrumentForFlaskRestx):
    nom: str
    prenom: str
    civilite: str
    role: str
    telephone: str
    email: str


@dataclass
class ActionProposee(metaclass=_InstrumentForFlaskRestx):
    intitule: str
    objectifs: str


@dataclass
class Subvention(metaclass=_InstrumentForFlaskRestx):
    ej: str
    service_instructeur: str
    dispositif: str
    sous_dispositif: str
    montant_demande: float
    montant_accorde: float

    actions_proposees: list[ActionProposee]

    def __post_init__(self):
        # Vérification et transformation des valeurs pour 'montant_demande' et 'montant_accorde'
        if isinstance(self.montant_demande, str) and self.montant_demande == "":
            self.montant_demande = 0

        if isinstance(self.montant_accorde, str) and self.montant_accorde == "":
            self.montant_accorde = 0
