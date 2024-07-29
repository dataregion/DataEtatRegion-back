import json
import logging
from pathlib import Path

from flask import current_app, request, jsonify, make_response
from flask_restx import Namespace, Resource, reqparse
from flask_restx._http import HTTPStatus

from app.controller.financial_data.schema_model import register_demarche_schemamodel
from app.models.demarches.demarche import Demarche
from app.models.demarches.dossier import Dossier
from app.models.demarches.donnee import Donnee
from app.models.demarches.valeur_donnee import ValeurDonnee
from app.servicesapp.api_externes import ApisExternesService
from app.services.demarches.demarches import DemarcheService, commit_session
from app.services.demarches.donnees import DonneeService
from app.services.demarches.dossiers import DossierService
from app.services.demarches.valeurs import ValeurService


api = Namespace(
    name="Démarches", path="/", description="Api de gestion des données récupérées de l'API Démarches Simplifiées"
)

model_demarche_single_api = register_demarche_schemamodel(api)

auth = current_app.extensions["auth"]

service = ApisExternesService()

reqpars_get_demarche = reqparse.RequestParser()
reqpars_get_demarche.add_argument("id", type=int, help="ID de la démarche", location="form", required=True)


def get_query_from_file(query_filename: str):
    p = Path(__file__).resolve().parent / "queries" / query_filename
    with p.open("r") as f:
        query_str = f.read()
    return query_str


@api.route("/demarche")
class DemarcheSimplifie(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self):
        # Vérification si la démarche existe déjà en BDD, si oui on la supprime
        demarche_number = int(request.args["id"])
        demarche: Demarche = DemarcheService.find(demarche_number)
        return make_response(jsonify(demarche), HTTPStatus.OK)

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    @api.expect(reqpars_get_demarche)
    def post(self):
        # Vérification si la démarche existe déjà en BDD, si oui on la supprime
        demarche_number = int(request.form["id"])
        demarche = DemarcheService.exists(demarche_number)
        if DemarcheService.exists(demarche_number):
            DemarcheService.delete(demarche)
            logging.info("[API DEMARCHES] La démarche existait déjà en BDD, maintenant supprimée pour réintégration")

        # Récupération des données de la démarche via l'API Démarches Simplifiées
        query = get_query_from_file("get_demarche.gql")
        data = {
            "operationName": "getDemarche",
            "query": query,
            "variables": {"demarcheNumber": demarche_number, "includeRevision": True},
        }
        demarche_dict = service.api_demarche_simplifie.do_post(json.dumps(data))
        logging.info("[API DEMARCHES] Récupération de la Démarche")

        # Sauvegarde de la démarche
        demarche: Demarche = DemarcheService.save(demarche_number, demarche_dict)
        logging.info(f"[API DEMARCHES] Sauvegarde de la démarche {demarche_number}")

        # Sauvegarde des dossiers de la démarche
        if len(demarche_dict["data"]["demarche"]["dossiers"]):
            # Insertion des dossiers et des valeurs des champs du dossier
            for dossier_dict in demarche_dict["data"]["demarche"]["dossiers"]["nodes"]:
                donnees: list[Donnee] = DossierService.get_donnees(
                    dossier_dict, demarche.number, demarche_dict["data"]["demarche"]["revisions"]
                )

                # Sauvegarde du dossier
                dossier: Dossier = DossierService.save(demarche_number, dossier_dict)
                logging.info(f"[API DEMARCHES] Sauvegarde du dossier {dossier_dict['number']}")

                for champ in dossier_dict["champs"]:
                    ValeurService.save(dossier.number, map(lambda d: d.section_name == "champ", donnees), champ)

                for annot in dossier_dict["annotations"]:
                    ValeurService.save(dossier.number, map(lambda d: d.section_name == "annotation", donnees), champ)

            logging.info("[API DEMARCHES] Sauvegarde des dossiers en BDD")

        commit_session()
        return make_response(jsonify(demarche), HTTPStatus.OK)


@api.route("/reconciliation")
class DemarchesReconciliation(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    @api.expect(reqpars_get_demarche)
    def post(self):
        # Vérification si la démarche existe déjà en BDD, si oui on la supprime
        demarche_number = int(request.form["id"])
        if not DemarcheService.exists(demarche_number):
            logging.info("[API DEMARCHES] La démarche n'existe pas")
            return HTTPStatus.NOT_FOUND

        # Récupération des données de la démarche via l'API Démarches Simplifiées
        reconciliation = {}
        if "champEJ" in request.form:
            reconciliation["champEJ"] = request.form["champEJ"]
        elif "champDS" in request.form:
            reconciliation["champDS"] = request.form["champDS"]
        elif "champSiret" in request.form and "champMontant" in request.form:
            if "centreCouts" in request.form:
                reconciliation["centreCouts"] = request.form["centreCouts"]
            if "domaineFonctionnel" in request.form:
                reconciliation["domaineFonctionnel"] = request.form["domaineFonctionnel"]
            if "refProg" in request.form:
                reconciliation["refProg"] = request.form["refProg"]
            if "annee" in request.form:
                reconciliation["annee"] = request.form["annee"]

            if "commune" in request.form:
                reconciliation["commune"] = request.form["commune"]
            if "epci" in request.form:
                reconciliation["epci"] = request.form["epci"]
            if "departement" in request.form:
                reconciliation["departement"] = request.form["departement"]
            if "region" in request.form:
                reconciliation["region"] = request.form["region"]

            reconciliation["champSiret"] = request.form["champSiret"]
            reconciliation["champMontant"] = request.form["champMontant"]

        DemarcheService.update_reconciliation(demarche_number, reconciliation)
        logging.info("[API DEMARCHES] Sauvegarde de la reconciliation de la Démarche en BDD")

        return make_response(jsonify(DemarcheService.find(demarche_number)), HTTPStatus.OK)


@api.route("/affichage")
class DemarchesAffichage(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    @api.expect(reqpars_get_demarche)
    def post(self):
        # Vérification si la démarche existe déjà en BDD, si oui on la supprime
        demarche_number = int(request.form["id"])
        if not DemarcheService.exists(demarche_number):
            logging.info("[API DEMARCHES] La démarche n'existe pas")
            return HTTPStatus.NOT_FOUND

        # Récupération des données de la démarche via l'API Démarches Simplifiées
        affichage = {}
        if "nomProjet" in request.form:
            affichage["nomProjet"] = request.form["nomProjet"]
        if "descriptionProjet" in request.form:
            affichage["descriptionProjet"] = request.form["descriptionProjet"]
        if "categorieProjet" in request.form:
            affichage["categorieProjet"] = request.form["categorieProjet"]
        if "coutProjet" in request.form:
            affichage["coutProjet"] = request.form["coutProjet"]
        if "montantDemande" in request.form:
            affichage["montantDemande"] = request.form["montantDemande"]
        if "montantAccorde" in request.form:
            affichage["montantAccorde"] = request.form["montantAccorde"]
        if "dateFinProjet" in request.form:
            affichage["dateFinProjet"] = request.form["dateFinProjet"]
        if "contact" in request.form:
            affichage["contact"] = request.form["contact"]

        DemarcheService.update_affichage(demarche_number, affichage)
        logging.info("[API DEMARCHES] Sauvegarde de la reconciliation de la Démarche en BDD")

        return make_response(jsonify(DemarcheService.find(demarche_number)), HTTPStatus.OK)


@api.route("/donnees")
class Donnees(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self):
        """
        Récupération des données d'une démarche
        Returns: Response
        """
        demarche_number = int(request.args["id"])
        donnees: list[Donnee] = [row for row in DonneeService.find_by_demarche(demarche_number)]
        return make_response(jsonify(donnees), HTTPStatus.OK)


@api.route("/valeurs")
class ValeurDonneeSimplifie(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self):
        """
        Récupération des valeurs d
        Returns: Response
        """
        demarche_number = int(request.args["idDemarche"])
        statutDossier = request.args["statutDossier"]
        idDonnees: list[str] = request.args["idDonnees"].split(",")
        dossiers: list[int] = [row.number for row in DossierService.find_by_demarche(demarche_number, statutDossier)]

        valeurs: list[ValeurDonnee] = []
        for idDonnee in idDonnees:
            valeurs.extend(ValeurService.find_by_dossiers(dossiers, int(idDonnee)))

        return make_response(jsonify(valeurs), HTTPStatus.OK)
