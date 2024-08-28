import logging
import requests

from flask import make_response, current_app
from flask_restx._http import HTTPStatus

from flask_restx import Namespace, Resource, abort, inputs

from app.clients.keycloack.factory import make_or_get_keycloack_admin, KeycloakConfigurationException
from app.controller import ErrorController
from app.controller.Decorators import check_permission
from app.controller.utils.ControllerUtils import get_pagination_parser
from app.models.common.Pagination import Pagination
from app.models.enums.AccountRole import AccountRole
from app.servicesapp.authentication import ConnectedUser

from keycloak import KeycloakAdmin

SOFT_DISABLED_KEY = "soft-disabled"

api = Namespace(name="users", path="/users", description="API de gestion des utilisateurs")
parser_get = get_pagination_parser()
parser_get.add_argument(
    "only_disable",
    type=inputs.boolean,
    required=False,
    default=False,
    help="Uniquement les utilisateurs non actif ou non",
)

auth = current_app.extensions["auth"]


@api.errorhandler(KeycloakConfigurationException)
def handler_keycloak_exception(error):
    message = "Erreur keycloak"
    if hasattr(error, "message"):
        message = error.message
    return ErrorController(message).to_json(), HTTPStatus.INTERNAL_SERVER_ERROR


@api.route("")
class UsersManagement(Resource):
    """
    Resource for managing users.
    """

    @api.response(200, "List of users and pagination information")
    @api.doc(security="Bearer")
    @api.expect(parser_get)
    @auth.token_auth("default", scopes_required=["openid"])
    @check_permission(AccountRole.ADMIN)
    def get(self):
        """
        Retourne la liste des utilisateurs
        """
        user = ConnectedUser.from_current_token_identity()

        p_args = parser_get.parse_args()
        page_number = p_args.get("page_number")
        limit = p_args.get("limit")
        if page_number < 1:
            page_number = 1
        if limit < 0:
            limit = 1
        only_disable = p_args.get("only_disable")

        logging.debug(f"[USERS] Call users get with limit {limit}, page {page_number}, only_disable {only_disable}")
        source_region = user.current_region
        source_region_groups_ids = _fetch_groups_ids(source_region)
        keycloak_admin = make_or_get_keycloack_admin()
        users = []
        for group_id in source_region_groups_ids:
            users = users + keycloak_admin.get_group_members(group_id, {"briefRepresentation": False})

        for user in users:
            user["softEnabled"] = True
            is_soft_disabled = user.get("attributes", {}).get(SOFT_DISABLED_KEY, [False])[0] == "true"
            is_disabled = user.get("enabled", True) is False
            if is_soft_disabled or is_disabled:
                user["softEnabled"] = False

        if only_disable:
            logging.debug("[USERS] get only disabled users")
            users = list(filter(lambda user: user["softEnabled"] is False, users))

        users = _filter_unique_by_attribute(users, "id")

        debut_index = (page_number - 1) * limit
        fin_index = debut_index + limit
        users_to_return = users[debut_index:fin_index]

        return {
            "users": users_to_return,
            "pageInfo": Pagination(users.__len__(), page_number, users_to_return.__len__()).to_json(),
        }, HTTPStatus.OK


@api.route("/<uuid>")
class UserDelete(Resource):
    @api.response(200, "Success")
    @api.response(400, "Utilisateur est activé")
    @api.doc(security="Bearer")
    @auth.token_auth("default", scopes_required=["openid"])
    @check_permission(AccountRole.ADMIN)
    def delete(self, uuid):
        """
        Supprime l'utilisateur si il est désactivé et appartient à la region de l'admin
        """
        user = ConnectedUser.from_current_token_identity()
        source_region = user.current_region
        logging.debug(f"[USERS] Call delete users {uuid}")
        keycloak_admin = make_or_get_keycloack_admin()
        # on récupère l'utilisateur
        user = keycloak_admin.get_user(uuid)
        _soft_disable_an_user(uuid, source_region, keep_groups=False)

        return "Success", HTTPStatus.OK


@api.route("/<uuid>/disable")
class UsersDisable(Resource):
    @api.response(200, "Success")
    @api.doc(security="Bearer")
    @auth.token_auth("default", scopes_required=["openid"])
    @check_permission(AccountRole.ADMIN)
    def patch(self, uuid):
        """
        Désactive un utilisateur
        """
        user = ConnectedUser.from_current_token_identity()

        logging.debug(f"[USERS] Call disable users {uuid}")
        source_region = user.current_region

        # on check si l'utilisateur est bien dans un groupes de la région
        if not _user_belong_region(uuid, source_region):
            return ErrorController("L'utilisateur ne fait pas partie de la région").to_json(), HTTPStatus.BAD_REQUEST

        if user.sub == uuid:
            return abort(message="Vous ne pouvez désactiver votre utilisateur", code=HTTPStatus.FORBIDDEN)

        _soft_disable_an_user(uuid, source_region)
        return make_response("", 200)


@api.route("/<uuid>/enable")
class UsersEnable(Resource):
    @api.response(200, "Success")
    @api.doc(security="Bearer")
    @auth.token_auth("default", scopes_required=["openid"])
    @check_permission(AccountRole.ADMIN)
    def patch(self, uuid):
        """
        Active un compte utilisateur
        """
        user = ConnectedUser.from_current_token_identity()
        logging.debug(f"[USERS] Call enable users {uuid}")
        source_region = user.current_region

        _soft_enable_user(uuid, source_region)
        return make_response("", 200)


def _fetch_subgroups(keycloak_admin: KeycloakAdmin, parent_id):
    """
    WORKAROUND : Récupération des subgroups en appelant directement l'API Admin de Keycloak
    - Les subgroups ne sont plus retournés via le endpoint /groups
    - Appel direct à l'API Keycloak en attendant une maj du package python-keycloak
    ISSUE : https://github.com/marcospereirampj/python-keycloak/issues/509
    """
    keycloak_admin.realm_name
    endpoint = (
        keycloak_admin.server_url + "/admin/realms/" + keycloak_admin.realm_name + "/groups/" + parent_id + "/children"
    )
    headers = {"Authorization": "Bearer " + keycloak_admin.token["access_token"]}
    return requests.get(endpoint, headers=headers).json()


def _fetch_groups_ids(source_region: str) -> list:
    groups = _fetch_groups(source_region)
    groups_ids = []
    for group in groups:
        groups_ids.append(group["id"])
    return groups_ids


def _fetch_groups(source_region: str) -> list:
    """
    Récupérer les groupes ids d'une région
    :param source_region:
    :param include_soft_disabled: Inclue les utilisateurs soft-disabled
    :return: une grappe de groupe avec la racine en première position
    """
    keycloak_admin = make_or_get_keycloack_admin()
    logging.debug(f"[USERS] Get groups for region {source_region}")

    groups = keycloak_admin.get_groups({"q": f"region:{source_region}"})
    if groups is None:
        logging.warning(f"[USERS] Group for region {source_region} not found")
        return abort(message="admin_exception.message", code=HTTPStatus.BAD_REQUEST)
    assembled_groups = [groups[0]]
    if groups[0]["subGroupCount"] != 0:
        subgroups = _fetch_subgroups(keycloak_admin, groups[0]["id"])
        for subgroup in subgroups:
            assembled_groups.append(subgroup)
    return assembled_groups


def _user_belong_region(uuid, source_region: str) -> bool:
    """
    Pour un uuid utilisateur, vérifie si il appartient à un groupe de la region
    :param uuid: uuid de l'utilisateur
    :param source_region:
    :return:
    """
    keycloak_admin = make_or_get_keycloack_admin()
    # on récupères les groups de l'utilisateur
    groups_belong_user = keycloak_admin.get_user_groups(uuid)
    groups_id_belong_user = [g["id"] for g in groups_belong_user]
    # on récupère les groups de la region
    groups_id_region = _fetch_groups_ids(source_region)
    return bool(set(groups_id_belong_user) & set(groups_id_region))


def _soft_disable_an_user(uuid, source_region: str, keep_groups=None):
    if keep_groups is None:
        keep_groups = True
    erase_groups = not keep_groups

    keycloak_admin = make_or_get_keycloack_admin()

    user = keycloak_admin.get_user(uuid)
    user["attributes"][SOFT_DISABLED_KEY] = ["true"]
    keycloak_admin.update_user(uuid, payload=user)
    if erase_groups:
        region_groups = _fetch_groups(source_region)
        for group in region_groups:
            keycloak_admin.group_user_remove(uuid, group["id"])


def _soft_enable_user(uuid, source_region: str):
    groups = _fetch_groups(source_region)
    if len(groups) < 1:
        return (
            ErrorController(f"Pas de groupe correspondant à la source region {source_region}").to_json(),
            HTTPStatus.BAD_REQUEST,
        )

    groupe_racine = groups[0]
    groupe_racine_id = groupe_racine["id"]

    keycloak_admin = make_or_get_keycloack_admin()
    user = keycloak_admin.get_user(user_id=uuid)
    user["attributes"][SOFT_DISABLED_KEY] = ["false"]
    user["enabled"] = True
    keycloak_admin.update_user(user_id=uuid, payload=user)  # XXX enabled True nécessaire pour la retro compatiblité.
    add_response = keycloak_admin.group_user_add(uuid, groupe_racine_id)
    logging.info(f"Ajout de l'utilisateur {uuid} au groupe {groupe_racine['path']}")
    logging.debug(f"Keycloak response: {add_response}")


def _filter_unique_by_attribute(data, attribute):
    seen = set()
    unique_data = []

    for item in data:
        attr_value = item[attribute]
        if attr_value not in seen:
            unique_data.append(item)
            seen.add(attr_value)

    return unique_data


def _find_first_by_attribute(data, attribute, value):
    for item in data:
        if item[attribute] == value:
            return item
    return None  # If no match is found
