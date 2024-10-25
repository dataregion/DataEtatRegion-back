from models import _PersistenceBaseModelInstance
from models.entities.common.Audit import _Audit
from sqlalchemy import Column, Integer, String


class Region(_Audit, _PersistenceBaseModelInstance()):
    __tablename__ = "ref_region"
    id = Column(Integer, primary_key=True)
    code = Column(String, unique=True, nullable=False)
    label = Column(String)


comp_code_region = {
    "ADCE": "00",  # Administration centrale
    "ALSA": "44",  # Alsace => Grand Est
    "AQUI": "75",  # Aquitaine => Nouvelle-Aquitaine
    "AUVE": "84",  # Auvergne => Auvergne-Rhône-Alpes
    "BNOR": "28",  # Basse-Normandie => Normandie
    "BOUR": "27",  # Bourgogne => Bourgogne-Franche-Comté
    "BRET": "53",  # Bretagne ==
    "CENT": "24",  # Centre => Centre-Val de Loire
    "CHAR": "44",  # Champagne-Ardennes => Grand Est
    "CORS": "94",  # Corse ==
    "DOM1": "01",  # Guadeloupe (DOM)
    "DOM2": "02",  # Martinique (DOM)
    "DOM3": "03",  # Guyane (DOM)
    "DOM4": "04",  # La Réunion (DOM)
    "ETR1": "99",  # Étranger
    "FRCO": "27",  # Franche-Comté => Bourgogne-Franche-Comté
    "HNOR": "28",  # Haute-Normandie => Normandie
    "IDF1": "11",  # Île-de-France ==
    "LANG": "76",  # Languedoc-Roussillon => Occitanie
    "LIMO": "75",  # Limousin => Nouvelle-Aquitaine
    "LORR": "44",  # Lorraine => Grand Est
    "MIPY": "76",  # Midi-Pyrénées => Occitanie
    "NORP": "32",  # Nord-Pas-de-Calais => Hauts-de-France
    "PACA": "93",  # Provence-Alpes-Côte d'Azur ==
    "PAYL": "52",  # Pays de la Loire ==
    "PICA": "32",  # Picardie => Hauts-de-France
    "POIT": "75",  # Poitou-Charentes => Nouvelle-Aquitaine
    "RALP": "84",  # Rhône-Alpes => Auvergne-Rhône-Alpes
}


def get_code_region_by_code_comp(code_comp):
    return comp_code_region.get(code_comp)