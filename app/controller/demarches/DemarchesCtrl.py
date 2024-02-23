import json
from flask import jsonify, current_app, request
from flask_restx import Namespace, Resource, reqparse
from flask_restx._http import HTTPStatus
from werkzeug.datastructures import FileStorage

import logging

from app.controller.Decorators import check_permission
from app.controller.financial_data import check_file_import
from app.controller.financial_data.schema_model import register_demarche_schemamodel
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.common.Pagination import Pagination
from app.models.enums.AccountRole import AccountRole
from app.models.financial.Ademe import AdemeSchema
from app.servicesapp.api_externes import ApisExternesService
from app.servicesapp.authentication import ConnectedUser
from app.servicesapp.financial_data import import_ademe, search_ademe, get_ademe

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
        query = """
            query getDemarche($demarcheNumber: Int!) {
                demarche(number: $demarcheNumber) {
                    title
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

        data = {
            "operationName": "getDemarche",
            "query": query,
            "variables": {"demarcheNumber": int(request.form["id"])},
        }

        demarche_dict = service.api_demarche_simplifie.do_post(json.dumps(data))

        demarche_data = {"number": request.form["id"], "title": demarche_dict["data"]["demarche"]["title"]}
        # demarche = Demarche(demarche_data)

        logging.info(demarche_dict)
        logging.info(type(demarche_dict))
        return demarche_dict
        # return {"message": "Demarche saved", "status": 200}
