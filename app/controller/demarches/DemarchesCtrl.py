import json
import logging
from pathlib import Path

from flask import current_app, request, jsonify, make_response
from flask_restx import Namespace, Resource, reqparse
from flask_restx._http import HTTPStatus

from app.controller.financial_data.schema_model import register_demarche_schemamodel
from app.models.demarches.demarche import Demarche
from app.models.demarches.donnee import Donnee
from app.models.demarches.dossier import Dossier
from app.models.demarches.reconciliation import Reconciliation
from app.models.demarches.valeur_donnee import ValeurDonnee
from app.services.demarches.affichage import AffichageService
from app.services.demarches.demarches import DemarcheService, commit_session
from app.services.demarches.donnees import DonneeService
from app.services.demarches.dossiers import DossierService
from app.services.demarches.reconciliations import ReconciliationService
from app.services.demarches.valeurs import ValeurService
from app.servicesapp.api_externes import ApisExternesService

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
        demarche = DemarcheService.find(demarche_number)
        if demarche is not None:
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
                    ValeurService.save(dossier.number, [d for d in donnees if d.section_name == "champ"], champ)

                for annot in dossier_dict["annotations"]:
                    ValeurService.save(dossier.number, [d for d in donnees if d.section_name == "annotation"], annot)

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
        champs_reconciliation = dict()
        cadre = dict()
        if "champEJ" in request.form:
            champs_reconciliation["champEJ"] = int(request.form["champEJ"])
        elif "champDS" in request.form:
            champs_reconciliation["champDS"] = int(request.form["champDS"])
        elif "champSiret" in request.form and "champMontant" in request.form:
            champs_reconciliation["champSiret"] = int(request.form["champSiret"])
            champs_reconciliation["champMontant"] = int(request.form["champMontant"])
            if "centreCouts" in request.form:
                cadre["centreCouts"] = request.form["centreCouts"]
            if "domaineFonctionnel" in request.form:
                cadre["domaineFonctionnel"] = request.form["domaineFonctionnel"]
            if "refProg" in request.form:
                cadre["refProg"] = request.form["refProg"]
            if "annee" in request.form:
                cadre["annee"] = int(request.form["annee"])
            if "commune" in request.form:
                cadre["commune"] = request.form["commune"]
            if "epci" in request.form:
                cadre["epci"] = request.form["epci"]
            if "departement" in request.form:
                cadre["departement"] = request.form["departement"]
            if "region" in request.form:
                cadre["region"] = request.form["region"]
        ReconciliationService.do_reconciliation(int(request.form["id"]), champs_reconciliation, cadre)
        logging.info("[API DEMARCHES] Sauvegarde de la reconciliation de la Démarche en BDD")

        return make_response(jsonify(DemarcheService.find(demarche_number)), HTTPStatus.OK)

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self):
        demarche_number = int(request.args["id"])
        reconciliations: list[Reconciliation] = [
            row for row in ReconciliationService.find_by_demarche_number(demarche_number)
        ]
        return make_response(jsonify(reconciliations), HTTPStatus.OK)


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
            affichage["nomProjet"] = int(request.form["nomProjet"])
        if "descriptionProjet" in request.form:
            affichage["descriptionProjet"] = int(request.form["descriptionProjet"])
        if "categorieProjet" in request.form:
            affichage["categorieProjet"] = int(request.form["categorieProjet"])
        if "coutProjet" in request.form:
            affichage["coutProjet"] = int(request.form["coutProjet"])
        if "montantDemande" in request.form:
            affichage["montantDemande"] = int(request.form["montantDemande"])
        if "montantAccorde" in request.form:
            affichage["montantAccorde"] = int(request.form["montantAccorde"])
        if "dateFinProjet" in request.form:
            affichage["dateFinProjet"] = int(request.form["dateFinProjet"])
        if "contact" in request.form:
            affichage["contact"] = int(request.form["contact"])

        DemarcheService.update_affichage(demarche_number, affichage)
        logging.info("[API DEMARCHES] Sauvegarde de la reconciliation de la Démarche en BDD")

        return make_response(jsonify(DemarcheService.find(demarche_number)), HTTPStatus.OK)

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self):
        financial_ae_id = int(request.args["financialAeId"])
        affichage = AffichageService.get_affichage_by_finance_ae_id(financial_ae_id)
        if affichage is None:
            return HTTPStatus.NOT_FOUND
        return make_response(jsonify(affichage), HTTPStatus.OK)


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
        Récupération des valeurs
        Returns: Response
        """
        demarche_number = int(request.args["idDemarche"])
        statutDossier = request.args["statutDossier"]
        idDonnees: list[str] = request.args["idDonnees"].split(",")
        dossiers: list[int] = [
            dossier[0].number for dossier in DossierService.find_by_demarche(demarche_number, statutDossier)
        ]

        valeurs: list[ValeurDonnee] = []
        for idDonnee in idDonnees:
            valeurs.extend(ValeurService.find_by_dossiers(dossiers, int(idDonnee)))

        return make_response(jsonify(valeurs), HTTPStatus.OK)
