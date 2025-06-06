"""
This controller defines a Flask-RESTX Namespace called "preferences" with an endpoint for managing user preferences. The `/users/preferences` path is used for the namespace. The `post` method allows to create a new preference for the current user while the `get` method allows to retrieve the list of preferences for the current user. The `oidc` library is used for authentication and the `marshmallow` library is used for input validation.

The `preference` and `preference_get` models are used to define the expected input and output for the `post` and `get` methods respectively.

The `PreferenceUsers` class, which inherits from `Resource`, is responsible for handling the `post` and `get` methods, and it has the decorators to handle the request validation, token validation, and request/response serialization.
"""

import datetime
import logging
from http import HTTPStatus

from models.schemas.preferences import PreferenceFormSchema, PreferenceSchema
import sqlalchemy
from flask_restx import Namespace, Resource, fields, abort, reqparse
from flask import request, current_app
from marshmallow import ValidationError
from sqlalchemy import cast
from sqlalchemy.orm import lazyload

from app import db
from app.clients.keycloack.factory import make_or_get_keycloack_admin, KeycloakConfigurationException
from app.controller.utils.ControllerUtils import get_origin_referrer
from models.entities.preferences.Preference import Preference, Share
from app.servicesapp.authentication import ConnectedUser

api = Namespace(
    name="preferences", path="/users/preferences", description="API de gestion des préférences utilisateurs"
)
auth = current_app.extensions["auth"]

preference = api.model(
    "CreateUpdatePreference",
    {
        "name": fields.String(required=True, description="Name of the preference"),
        "uuid": fields.String(required=False, description="Uuid of the preference for update"),
        "filters": fields.Wildcard(fields.Raw, description="JSON object representing the user's filter"),
        "shares": fields.List(
            fields.Nested(
                api.model(
                    "shares",
                    {
                        "shared_username_email": fields.String(required=True, description="Courriel d'un utilisateur"),
                    },
                ),
                required=False,
            ),
            required=False,
        ),
    },
)

preference_get = api.model(
    "Preference",
    {
        "name": fields.String(required=True, description="Name of the preference"),
        "username": fields.String(required=True, description="Creator of the preference"),
        "uuid": fields.String(required=True, description="Uuid of the preference"),
        "filters": fields.Wildcard(fields.Raw, description="JSON object representing the user's filter"),
        "shares": fields.List(
            fields.Nested(
                api.model(
                    "shares",
                    {
                        "shared_username_email": fields.String(required=True, description="Courriel d'un utilisateur"),
                    },
                ),
                required=False,
            ),
            required=False,
        ),
    },
)

list_preference_get = api.model(
    "Preference_Share",
    {
        "create_by_user": fields.List(fields.Nested(preference_get)),
        "shared_with_user": fields.List(fields.Nested(preference_get)),
    },
)


@api.route("")
class PreferenceUsers(Resource):
    """
    Resource for managing users.
    """

    @api.response(200, "The preference created", preference)
    @api.doc(security="Bearer")
    @api.expect(preference)
    @auth("openid")
    def post(self):
        """
        Create a new preference for the current user
        """
        user = ConnectedUser.from_current_token_identity()
        clientId = user.azp

        from app.tasks.management_tasks import share_filter_user

        logging.debug("[PREFERENCE][CTRL] Post users prefs")
        json_data = request.get_json()
        json_data["username"] = user.username

        schema_create_validation = PreferenceFormSchema()
        try:
            data = schema_create_validation.load(json_data)
        except ValidationError as err:
            logging.error(f"[PREFERENCE][CTRL] {err.messages}")
            return {"message": "Invalid", "details": err.messages}, HTTPStatus.BAD_REQUEST

        # on retire les shares pour soit même.
        shares = list(filter(lambda d: d["shared_username_email"] != json_data["username"], data["shares"]))

        share_list = [Share(**share) for share in shares]
        application = get_origin_referrer(request)
        pref = Preference(
            username=data["username"],
            name=data["name"],
            options=data["options"],
            filters=data["filters"],
            application_clientid=clientId,
        )
        pref.shares = share_list

        try:
            db.session.add(pref)
            logging.info(f'[PREFERENCE][CTRL] Adding preference for user {json_data["username"]}')
            db.session.commit()

            if len(pref.shares) > 0:
                share_filter_user.delay(str(pref.uuid), application)
        except Exception as e:
            logging.error("[PREFERENCE][CTRL] Error when saving preference", e)
            return abort(message="Error when saving preference", code=HTTPStatus.BAD_REQUEST)

        return PreferenceSchema().dump(pref)

    @auth("openid")
    @api.doc(security="Bearer")
    @api.response(200, "List of the user's preferences", [list_preference_get])
    def get(self):
        """
        Retrieve the list
        """
        user = ConnectedUser.from_current_token_identity()
        clientId = user.azp

        logging.debug(f"get users prefs {clientId}")

        list_pref = (
            Preference.query.options(lazyload(Preference.shares))
            .filter_by(username=user.username, application_clientid=clientId)
            .order_by(Preference.id)
            .all()
        )
        list_pref_shared = (
            Preference.query.join(Share)
            .filter(Share.shared_username_email == user.username, Preference.application_clientid == clientId)
            .distinct(Preference.id)
            .all()
        )

        schema = PreferenceSchema(many=True)
        create_by_user = schema.dump(list_pref)
        shared_with_user = schema.dump(list_pref_shared)
        return {"create_by_user": create_by_user, "shared_with_user": shared_with_user}, HTTPStatus.OK


@api.route("/<uuid>")
class CrudPreferenceUsers(Resource):
    @auth("openid")
    @api.doc(security="Bearer")
    @api.response(200, "Success if delete")
    def delete(self, uuid):
        """
        Delete uuid preference
        """
        logging.debug(f"Delete users prefs {uuid}")
        user = ConnectedUser.from_current_token_identity()
        clientId = user.azp

        preference = Preference.query.filter(
            cast(Preference.uuid, sqlalchemy.String) == uuid, Preference.application_clientid == clientId
        ).one()

        if preference.username != user.username:
            return abort(message="Vous n'avez pas les droits de supprimer cette préférence", code=HTTPStatus.FORBIDDEN)

        try:
            db.session.delete(preference)
            db.session.commit()
            return "Success", HTTPStatus.OK
        except Exception as e:
            logging.error(f"[PREFERENCE][CTRL] Error when delete preference {uuid} {clientId}", e)
            return abort(message=f"Error when delete preference on application {clientId}", code=HTTPStatus.BAD_REQUEST)

    @auth("openid")
    @api.doc(security="Bearer")
    @api.expect(preference)
    @api.response(200, "Success if delete")
    def post(self, uuid):
        """
        Update uuid preference
        """
        from app.tasks.management_tasks import share_filter_user

        user = ConnectedUser.from_current_token_identity()
        clientId = user.azp

        application = get_origin_referrer(request)
        preference_to_save = Preference.query.filter(
            cast(Preference.uuid, sqlalchemy.String) == uuid, Preference.application_clientid == clientId
        ).one()

        if preference_to_save.username != user.username:
            return abort(message="Vous n'avez pas les droits de modifier cette préférence", code=HTTPStatus.FORBIDDEN)

        json_data = request.get_json()

        # filter the shares list to exclude the current user
        shares = list(filter(lambda d: d["shared_username_email"] != user.username, json_data["shares"]))
        # create a list of Share objects from the filtered shares
        new_share_list = [Share(**share) for share in shares]
        # initialize a list to store the final shares to save
        shares_to_save = []
        # create sets of existing and new shares, based on their shared_username_email values
        existing_shares = {s.shared_username_email for s in preference_to_save.shares}
        new_shares = {s.shared_username_email for s in new_share_list}

        # find shares to delete and add
        to_delete = existing_shares - new_shares
        to_add = new_shares - existing_shares

        # delete shares that are no longer in the new share list
        for current_share in preference_to_save.shares:
            if current_share.shared_username_email in to_delete:
                db.session.delete(current_share)

        # add new shares that were not in the existing share list
        for new_share in new_share_list:
            if new_share.shared_username_email in to_add:
                shares_to_save.append(new_share)

        # set the final shares for the preference to save
        preference_to_save.shares = shares_to_save + [
            s for s in preference_to_save.shares if s.shared_username_email not in to_delete
        ]

        preference_to_save.name = json_data["name"]
        try:
            db.session.commit()
            if len(preference_to_save.shares) > 0:
                # send task async
                share_filter_user.delay(str(preference_to_save.uuid), application)
            return "Success", HTTPStatus.OK
        except Exception as e:
            logging.error(f"[PREFERENCE][CTRL] Error when delete preference {uuid}", e)
            return abort(message="Error when delete preference", code=HTTPStatus.BAD_REQUEST)

    @auth("openid")
    @api.doc(security="Bearer")
    @api.response(200, "User preference", preference_get)
    def get(self, uuid):
        """
        Get by uuid preference
        """
        logging.debug(f"Get users prefs {uuid}")
        user = ConnectedUser.from_current_token_identity()
        clientId = user.azp

        preference = Preference.query.filter(
            cast(Preference.uuid, sqlalchemy.String) == uuid, Preference.application_clientid == clientId
        ).one()

        schema = PreferenceSchema()
        result = schema.dump(preference)
        try:
            preference.nombre_utilisation += 1
            preference.dernier_acces = datetime.datetime.utcnow()
            db.session.commit()
        except Exception as e:
            logging.warning(f"[PREFERENCE][CTRL] Error when update count usage preference {uuid}", e)

        return result, HTTPStatus.OK


parser_search = reqparse.RequestParser()
parser_search.add_argument("username", type=str, required=True, help="Username")


@api.route("/search-user")
class UsersSearch(Resource):
    @api.response(200, "Search user by email/username for sharing")
    @api.doc(security="Bearer")
    @api.expect(parser_search)
    @auth("openid")
    def get(self):
        """
        Search users by userName
        """
        p_args = parser_search.parse_args()
        search_username = p_args.get("username")

        if search_username is None or len(search_username) < 4:
            return {"users": []}, HTTPStatus.OK
        try:
            keycloak_admin = make_or_get_keycloack_admin()
            query = {"briefRepresentation": True, "enabled": True, "search": search_username}
            users = keycloak_admin.get_users(query)

            return [{"username": user["username"]} for user in users], HTTPStatus.OK
        except KeycloakConfigurationException as admin_exception:
            return admin_exception.message, HTTPStatus.BAD_REQUEST
