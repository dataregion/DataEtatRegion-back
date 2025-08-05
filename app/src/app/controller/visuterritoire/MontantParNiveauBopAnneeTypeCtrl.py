from flask import make_response, jsonify
from flask import current_app
from flask import send_file
from flask_restx import Namespace, Resource
from sqlalchemy import select
from app import db

from .utilities import try_advisory_lock, AdvisoryLockError

from models.schemas.visuterritoire import MontantParNiveauBopAnneeTypeSchema
import tempfile
import csv

from models.entities.visuterritoire.query.VuesVisuTerritoire import MontantParNiveauBopAnneeType


api = Namespace(
    name="Montant par niveau, bop, année et type",
    path="/montant_par_niveau_bop_annee_type",
    description="Extract pour la vue visuterritoire `montant_par_niveau_bop_annee_type`",
)

auth = current_app.extensions["auth"]


@api.route("/download")
class ZipExtract(Resource):
    def get(self):
        """Récupère les données de montant d'ae par niveau, bop, année et type"""
        session = db.session()
        try:
            with (
                try_advisory_lock(session, "montant_par_niveau_bop_annee_type"),
                tempfile.NamedTemporaryFile(mode="w+", newline="", delete=True) as file,
            ):

                schema = MontantParNiveauBopAnneeTypeSchema()
                fieldsnames = list(schema.fields.keys())

                stmt = select(MontantParNiveauBopAnneeType).execution_options(yield_per=1000)
                rows = db.session.scalars(stmt)

                writer = csv.DictWriter(file, fieldsnames)
                writer.writeheader()

                for row in rows:
                    line_payload = schema.dump(row)
                    writer.writerow(line_payload)  # type: ignore

                return send_file(file.name, as_attachment=True, download_name="extract.csv")
        except AdvisoryLockError as _:
            response = make_response(jsonify(error="Export en cours. Veuillez réessayer plus tard."), 503)
            response.headers["Retry-After"] = "300"  # 5 minutes
            return response
