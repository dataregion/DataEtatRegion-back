from flask import Blueprint
from flask_restx import Api, Namespace

from app.controller.ref_controller.RefController import build_ref_controller
from app.controller.ref_controller.RefCrte import api as crte_api
from app.controller.ref_controller.RefTags import api as api_tags
from app.controller.ref_controller.RefLocalisationInterministerielle import api as api_loc_interministerielle
from app.controller.utils.ControllerUtils import ParserArgument
from app.models.refs.arrondissement import Arrondissement

# models
from app.models.refs.centre_couts import CentreCouts
from app.models.refs.code_programme import CodeProgramme
from app.models.refs.domaine_fonctionnel import DomaineFonctionnel
from app.models.refs.groupe_marchandise import GroupeMarchandise
from app.models.refs.ministere import Ministere
from app.models.refs.qpv import Qpv
from app.models.refs.referentiel_programmation import ReferentielProgrammation
from app.controller.utils.LoginController import api as api_auth
from app.models.refs.siret import Siret

api_ref = Blueprint("api_ref", __name__)

authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}

api = Api(
    api_ref,
    doc="/doc",
    prefix="/api/v1",
    description="API de récupérations des référentiels de Budget",
    title="Référentiel Budget",
    authorizations=authorizations,
)

api_domaine = build_ref_controller(
    DomaineFonctionnel,
    Namespace(name="Domaine Fonctionnel", path="/domaine-fonct", description="API referentiels des Domaine"),
)

api_centre_cout = build_ref_controller(
    CentreCouts,
    Namespace(name="Centre couts", path="/centre-couts", description="API referentiels des Centre de couts"),
    cond_opt=(
        ParserArgument(CentreCouts.code, str, "Recherche sur le code du centre de coûts"),
        ParserArgument(CentreCouts.code_postal, str, "Recherche sur le code postal de la commune associée"),
    ),
)

api_groupe_marchandise = build_ref_controller(
    GroupeMarchandise,
    Namespace(
        name="Groupe Marchandise",
        path="/groupe-marchandise",
        description="API referentiels des groupes de marchandises",
    ),
    cond_opt=(
        ParserArgument(GroupeMarchandise.domaine, str, "Recherche sur le domaine"),
        ParserArgument(GroupeMarchandise.segment, str, "Recherche sur le segment"),
    ),
)

api_bop = build_ref_controller(
    CodeProgramme,
    Namespace(name="Code Programme", path="/programme", description="API referentiels des codes programmes"),
)

api_ref_programmation = build_ref_controller(
    ReferentielProgrammation,
    Namespace(
        name="Referentiel Programmation",
        path="/ref-programmation",
        description="API referentiels des referentiel de programmation",
    ),
    cond_opt=(
        ParserArgument(ReferentielProgrammation.code, str, "Recherche sur le(s) code(s)", "split"),
        ParserArgument(
            ReferentielProgrammation.code_programme, str, "Recherche sur le(s) code(s) BOP associé(s)", "split"
        ),
    ),
)

api_ref_ministere = build_ref_controller(
    Ministere, Namespace(name="Ministere", path="/ministere", description="API referentiels des ministères")
)

api_ref_arrondissement = build_ref_controller(
    Arrondissement,
    Namespace(name="Arrondissement", path="/arrondissement", description="API referentiels des arrondissements"),
)

api_ref_beneficiaire = build_ref_controller(
    Siret,
    Namespace(name="Beneficiaire", path="/beneficiaire", description="API pour rechercher les beneficiares (siret)"),
    cond_opt=(ParserArgument(Siret.denomination, str, "Recherche sur la dénomation du SIRET"),),
)

api_ref_qpv = build_ref_controller(
    Qpv,
    Namespace(
        name="Quartier Prioritaire de la politique de la ville",
        path="/qpv",
        description="API pour lister les QPV en France",
    ),
    cond_opt=(
        ParserArgument(Qpv.label_commune, str, "Recherche sur le label de la commune associée"),
        ParserArgument(Qpv.annee_decoupage, int, "Recherche sur l'année de découpage des QPV"),
    ),
)


api.add_namespace(api_auth)

api.add_namespace(api_ref_ministere)
api.add_namespace(api_bop)
api.add_namespace(api_loc_interministerielle)
api.add_namespace(api_ref_programmation)
api.add_namespace(api_domaine)
api.add_namespace(api_centre_cout)
api.add_namespace(api_groupe_marchandise)
api.add_namespace(crte_api)
api.add_namespace(api_ref_arrondissement)
api.add_namespace(api_ref_beneficiaire)
api.add_namespace(api_tags)
api.add_namespace(api_ref_qpv)
