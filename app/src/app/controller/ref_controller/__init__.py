from app.controller import ApiDataEtat
from flask import Blueprint
from flask_restx import Namespace

from app.controller.ref_controller.RefController import build_ref_controller
from app.controller.ref_controller.RefCrte import api as crte_api
from app.controller.ref_controller.RefQpv import api as qpv_api
from app.controller.ref_controller.RefTags import api as api_tags
from app.controller.ref_controller.RefLocalisationInterministerielle import api as api_loc_interministerielle
from app.controller.utils.ControllerUtils import ParserArgument
from models.entities.refs.Arrondissement import Arrondissement

# models
from models.entities.refs.CentreCouts import CentreCouts
from models.entities.refs.CodeProgramme import CodeProgramme
from models.entities.refs.DomaineFonctionnel import DomaineFonctionnel
from models.entities.refs.GroupeMarchandise import GroupeMarchandise
from models.entities.refs.Ministere import Ministere
from models.entities.refs.ReferentielProgrammation import ReferentielProgrammation
from app.controller.utils.LoginController import api as api_auth
from models.entities.refs.Siret import Siret
from models.schemas.refs import (
    ArrondissementSchema,
    CentreCoutsSchema,
    CodeProgrammeSchema,
    DomaineFonctionnelSchema,
    GroupeMarchandiseSchema,
    MinistereSchema,
    ReferentielProgrammationSchema,
    SiretSchema,
)

api_ref = Blueprint("api_ref", __name__)

authorizations = {"Bearer": {"type": "apiKey", "in": "header", "name": "Authorization"}}

api = ApiDataEtat(
    api_ref,
    doc="/doc",
    prefix="/api/v1",
    description="API de récupérations des référentiels de Budget",
    title="Référentiel Budget",
    authorizations=authorizations,
)

api_domaine = build_ref_controller(
    DomaineFonctionnel,
    DomaineFonctionnelSchema,
    Namespace(name="Domaine Fonctionnel", path="/domaine-fonct", description="API referentiels des Domaine"),
)

api_centre_cout = build_ref_controller(
    CentreCouts,
    CentreCoutsSchema,
    Namespace(name="Centre couts", path="/centre-couts", description="API referentiels des Centre de couts"),
    cond_opt=(
        ParserArgument(CentreCouts.code, str, "Recherche sur le code du centre de coûts"),
        ParserArgument(CentreCouts.code_postal, str, "Recherche sur le code postal de la commune associée"),
    ),
)

api_groupe_marchandise = build_ref_controller(
    GroupeMarchandise,
    GroupeMarchandiseSchema,
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
    CodeProgrammeSchema,
    Namespace(name="Code Programme", path="/programme", description="API referentiels des codes programmes"),
)

api_ref_programmation = build_ref_controller(
    ReferentielProgrammation,
    ReferentielProgrammationSchema,
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
    Ministere,
    MinistereSchema,
    Namespace(name="Ministere", path="/ministere", description="API referentiels des ministères"),
)

api_ref_arrondissement = build_ref_controller(
    Arrondissement,
    ArrondissementSchema,
    Namespace(name="Arrondissement", path="/arrondissement", description="API referentiels des arrondissements"),
)

api_ref_beneficiaire = build_ref_controller(
    Siret,
    SiretSchema,
    Namespace(name="Beneficiaire", path="/beneficiaire", description="API pour rechercher les beneficiares (siret)"),
    cond_opt=(ParserArgument(Siret.denomination, str, "Recherche sur la dénomation du SIRET"),),
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
api.add_namespace(qpv_api)
