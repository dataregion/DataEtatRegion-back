from .MontantParNiveauBopAnneeTypeCtrl import api as montant_par_niveau_bop_annee_type_api
from .VueFrance2030 import api as vue_france_2030

from flask import Blueprint
from flask_restx import Api

api_visuterritoire_v1 = Blueprint("visuterritoire", __name__)

_description = "API pour l'interopérabilité avec visuterritoire"
api_v1 = Api(
    api_visuterritoire_v1,
    doc="/doc",
    prefix="/api/v1",
    description=_description,
    title="API visu territoire",
)

api_v1.add_namespace(montant_par_niveau_bop_annee_type_api)
api_v1.add_namespace(vue_france_2030)
