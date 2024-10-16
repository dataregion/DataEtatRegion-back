import logging

from app.models.demarches.affichage import AffichageDossier
from app.services.demarches.dossiers import DossierService
from app.services.demarches.valeurs import ValeurService

logger = logging.getLogger(__name__)


class AffichageService:
    @staticmethod
    def get_affichage_by_finance_ae_id(financial_ae_id):
        dossier = DossierService.find_by_financial_ae_id(financial_ae_id)
        if dossier is None:
            return None
        demarche = dossier.demarche
        param_affichage = demarche.affichage
        valeurs = ValeurService.get_dict_valeurs(dossier.number, param_affichage)
        affichage = AffichageDossier(
            nomDemarche=demarche.title,
            numeroDossier=dossier.number,
            nomProjet=AffichageService.get_valeur("nomProjet", param_affichage, valeurs),
            descriptionProjet=AffichageService.get_valeur("descriptionProjet", param_affichage, valeurs),
            categorieProjet=AffichageService.get_valeur("categorieProjet", param_affichage, valeurs),
            coutProjet=AffichageService.get_valeur("coutProjet", param_affichage, valeurs),
            montantDemande=AffichageService.get_valeur("montantDemande", param_affichage, valeurs),
            montantAccorde=AffichageService.get_valeur("montantAccorde", param_affichage, valeurs),
            dateFinProjet=AffichageService.get_valeur("dateFinProjet", param_affichage, valeurs),
            contact=AffichageService.get_valeur("contact", param_affichage, valeurs),
        )
        return affichage

    @staticmethod
    def get_valeur(nom_valeur, param_affichage, valeurs):
        if nom_valeur not in param_affichage:
            return None
        return valeurs.get(param_affichage[nom_valeur])
