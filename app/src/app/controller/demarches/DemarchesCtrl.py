import logging

from flask import current_app, request, jsonify, make_response
from flask_restx import Namespace, Resource, reqparse
from flask_restx._http import HTTPStatus

from app.controller.financial_data.schema_model import register_demarche_schemamodel
from app.services.demarches.affichage import AffichageService
from app.services.demarches.demarches import DemarcheService
from app.services.demarches.donnees import DonneeService
from app.services.demarches.dossiers import DossierService
from app.services.demarches.reconciliations import ReconciliationService
from app.services.demarches.tokens import TokenService
from app.services.demarches.valeurs import ValeurService
from app.servicesapp.authentication import ConnectedUser
from models.entities.demarches.Demarche import Demarche
from models.entities.demarches.Donnee import Donnee
from models.entities.demarches.Reconciliation import Reconciliation
from models.entities.demarches.ValeurDonnee import ValeurDonnee
from models.schemas.demarches import TokenSchema

api = Namespace(
    name="Démarches", path="/", description="Api de gestion des données récupérées de l'API Démarches Simplifiées"
)

model_demarche_single_api = register_demarche_schemamodel(api)

auth = current_app.extensions["auth"]

reqpars_get_demarche = reqparse.RequestParser()
reqpars_get_demarche.add_argument("id", type=int, help="ID de la démarche", location="form", required=True)


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
        user = ConnectedUser.from_current_token_identity()
        demarche = DemarcheService.integrer_demarche(user.sub, int(request.form["tokenId"]), int(request.form["id"]))
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
        elif "champMontant" in request.form:
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


@api.route("/token")
class TokenResource(Resource):
    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self):
        user = ConnectedUser.from_current_token_identity()
        tokens = TokenService.find_by_uuid_utilisateur(user.sub)
        return make_response(TokenSchema(many=True).dump(tokens), HTTPStatus.OK)

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def post(self):
        user = ConnectedUser.from_current_token_identity()
        nom = request.form.get("nom")
        token = request.form.get("token")
        return make_response(TokenSchema(many=False).dump(TokenService.create(nom, token, user.sub)), HTTPStatus.OK)

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def put(self):
        user = ConnectedUser.from_current_token_identity()
        token_id = int(request.form.get("id"))
        nom = request.form.get("nom")
        token = request.form.get("token")
        return make_response(
            TokenSchema(many=False).dump(TokenService.update(token_id, nom, token, user.sub)), HTTPStatus.OK
        )

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def delete(self):
        user = ConnectedUser.from_current_token_identity()
        token_id = int(request.args["id"])
        return make_response(TokenSchema(many=False).dump(TokenService.delete(token_id, user.sub)), HTTPStatus.OK)
