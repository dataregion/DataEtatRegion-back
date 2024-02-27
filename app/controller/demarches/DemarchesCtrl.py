import json
import logging

from flask import jsonify, current_app, request
from flask_restx import Namespace, Resource, reqparse
from flask_restx._http import HTTPStatus

from app.controller.Decorators import check_permission
from app.controller.financial_data import check_file_import
from app.controller.financial_data.schema_model import register_demarche_schemamodel
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.common.Pagination import Pagination
from app.models.demarches.demarche import Demarche
from app.models.demarches.dossier import Dossier
from app.models.demarches.donnee import Donnee
from app.models.enums.AccountRole import AccountRole
from app.models.financial.Ademe import AdemeSchema
from app.servicesapp.api_externes import ApisExternesService
from app.servicesapp.authentication import ConnectedUser
from app.services.demarches import demarche_exists, save_demarche, save_dossier, get_or_create_donnee, get_or_create_section, save_valeur_donnee

api = Namespace(
    name="Démarches", path="/", description="Api de gestion des données récupérées de l'API Démarches Simplifiées"
)

model_ademe_single_api = register_demarche_schemamodel(api)

auth = current_app.extensions["auth"]

service = ApisExternesService()

reqpars_get_demarche = reqparse.RequestParser()
reqpars_get_demarche.add_argument("id", type=int, help="ID de la démarche", location="form", required=True)


@api.route("/save")
class DemarcheSimplifie(Resource):
    # @auth.token_auth("default", scopes_required=["openid"])
    # @api.doc(security="Bearer")
    @api.expect(reqpars_get_demarche)
    def post(self):

        # Vérification si la démarche existe déjà en BDD
        demarche_number = int(request.form["id"])
        if demarche_exists(demarche_number):
            return {"message": "La démarche a déjà été intégrée.", "status": 200}

        # Requête GraphQL pour l'API Démarches Simplifiées
        query = """
            query getDemarche($demarcheNumber: Int!) {
                demarche(number: $demarcheNumber) {
                    title
                    chorusConfiguration {
                        centreDeCout
                        domaineFonctionnel
                        referentielDeProgrammation
                    }
                    dossiers {
                        nodes {
                            number
                            state
                            dateDerniereModification
                            champs {
                                label
                                __typename
                                stringValue
                            }
                            annotations {
                                label
                                __typename
                                stringValue
                            }
                            demandeur {
                                ... on PersonneMorale {
                                    siret
                                }
                            }
                        }
                    }
                }
            }
        """

        # Récupération des données de la démarche via l'API Démarches Simplifiées
        data = {
            "operationName": "getDemarche",
            "query": query,
            "variables": {"demarcheNumber": demarche_number},
        }
        demarche_dict = service.api_demarche_simplifie.do_post(json.dumps(data))
        logging.info(f"[API DEMARCHES] Récupération de la Démarche")

        # Sauvegarde des données de la démarche dans notre BDD
        demarche_data = {"number": request.form["id"], "title": demarche_dict["data"]["demarche"]["title"]}
        demarche: Demarche = save_demarche(Demarche(**demarche_data))
        logging.info(f"[API DEMARCHES] Sauvegarde de la Démarche en BDD")

        # Sauvegarde des dossiers de la démarche
        if len(demarche_dict["data"]["demarche"]["dossiers"]):

            # Récupération des champs et des annotations en amont de l'insert des dossiers
            donnees: dict[Donnee] = []
            for champ in demarche_dict["data"]["demarche"]["dossiers"]["nodes"][0]["champs"]:
                donnees.append(get_or_create_donnee(champ, "champ", demarche.number))
            for annot in demarche_dict["data"]["demarche"]["dossiers"]["nodes"][0]["annotations"]:
                donnees.append(get_or_create_donnee(annot, "annotation", demarche.number))
            logging.info(f"[API DEMARCHES] Récupération des champs et annotations des dossiers")

            # Insertion des dossiers et des valeurs des champs du dossier
            for dossier_dict in demarche_dict["data"]["demarche"]["dossiers"]["nodes"]:
                dossier_data = {
                    "number": dossier_dict["number"],
                    "state": dossier_dict["state"],
                    "date_derniere_modification": dossier_dict["dateDerniereModification"],
                    "demarche_number": demarche_number,
                    "siret": dossier_dict["demandeur"]["siret"]
                }
                dossier: Dossier = save_dossier(Dossier(**dossier_data))

                for champ in dossier_dict["champs"]:
                    donnee: Donnee = next((d for d in donnees if d.section_name == "champ" and d.type_name == champ["__typename"] and d.label == champ["label"]), None)
                    if donnee is not None:
                        save_valeur_donnee(dossier_dict["number"], donnee.id, champ["stringValue"])

                for annot in dossier_dict["annotations"]:
                    donnee: Donnee = next((d for d in donnees if d.section_name == "annotation" and d.type_name == champ["__typename"] and d.label == champ["label"]), None)
                    if donnee is not None:
                        save_valeur_donnee(dossier_dict["number"], donnee.id, annot["stringValue"])

            logging.info(f"[API DEMARCHES] Sauvegarde des dossiers en BDD")

        return {"message": "Démarche sauvegardée", "status": 200}
