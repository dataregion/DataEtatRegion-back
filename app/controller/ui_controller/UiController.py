from flask import current_app

from flask_restx import Namespace, Resource
from flask_pyoidc import OIDCAuthentication

from app import db

api = Namespace(
    name="UI",
    path="/",
    description="Controlleur qui fournit des données pour l4UI",
)

auth: OIDCAuthentication = current_app.extensions["auth"]


@api.route("/annees")
class GetYears(Resource):
    """
    Récupére la liste de toutes les années pour lesquelles on a des montants (engagés ou payés)
    :return:
    """

    @auth.token_auth("default", scopes_required=["openid"])
    @api.doc(security="Bearer")
    def get(self):
        annees = db.session.execute(
            db.text(
                """
            SELECT ARRAY(
                SELECT DISTINCT annee FROM public.financial_ae
                UNION
                SELECT DISTINCT annee FROM public.financial_cp
            )
        """
            )
        ).scalar_one_or_none()
        print(annees)
        if annees is None:
            return "", 204
        return annees, 200
