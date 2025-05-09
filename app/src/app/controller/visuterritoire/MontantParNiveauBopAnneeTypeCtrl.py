from flask import current_app
from flask import send_file
from flask_restx import Namespace, Resource

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

        schema = MontantParNiveauBopAnneeTypeSchema()
        rows = MontantParNiveauBopAnneeType.query.all()
        fieldsnames = list(schema.fields.keys())

        with tempfile.NamedTemporaryFile(mode="w+", newline="", delete=True) as file:
            writer = csv.DictWriter(file, fieldsnames)
            writer.writeheader()

            for row in rows:
                line_payload = schema.dump(row)
                writer.writerow(line_payload)  # type: ignore

            return send_file(file.name, as_attachment=True, download_name="extract.csv")
