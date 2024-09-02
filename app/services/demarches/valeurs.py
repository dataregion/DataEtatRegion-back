from app import db
from app.models.demarches.donnee import Donnee
from app.models.demarches.valeur_donnee import ValeurDonnee, ValeurDonneeSchema


class ValeurService:
    @staticmethod
    def find_by_dossiers(idDossiers: list[int], idDonnee: int) -> list[ValeurDonnee]:
        stmt = db.select(ValeurDonnee).where(
            ValeurDonnee.dossier_number.in_(idDossiers), ValeurDonnee.donnee_id == idDonnee
        )
        valeur_schema = ValeurDonneeSchema(many=True)
        return valeur_schema.dump(db.session.execute(stmt).scalars())

    @staticmethod
    def save(dossier_number: int, donnees: list[Donnee], champ: dict) -> ValeurDonnee:
        """
        Créé en BDD une valeur d'un champ pour un dossier
        :param dossier_number: Numéro du dossier associé
        :param donnee_id: ID de la donnée associée
        :param champ: Caractéristique du champ
        :return: Donnee
        """
        # Nom des champs additionnels à récupérer en fonction du type du champ
        _mappingTypes = [
            {"types": ["DateChamp"], "fields": ["date"]},
            {"types": ["DatetimeChamp"], "fields": ["datetime"]},
            {"types": ["CheckboxChamp"], "fields": ["checked"]},
            {"types": ["DecimalNumberChamp"], "fields": ["decimalNumber"]},
            {"types": ["IntegerNumberChamp", "NumberChamp"], "fields": ["integerNumber"]},
            {"types": ["CiviliteChamp"], "fields": ["civilite"]},
            {"types": ["LinkedDropDownListChamp"], "fields": ["primaryValue", "secondaryValue"]},
            {"types": ["MultipleDropDownListChamp"], "fields": ["values"]},
            {"types": ["PieceJustificativeChamp"], "fields": ["files"]},
            {"types": ["AddressChamp"], "fields": ["address"]},
            {"types": ["CommuneChamp"], "fields": ["commune", "departement"]},
            {"types": ["DepartementChamp"], "fields": ["departement"]},
            {"types": ["RegionChamp"], "fields": ["region"]},
            {"types": ["PaysChamp"], "fields": ["pays"]},
            {"types": ["SiretChamp"], "fields": ["etablissement"]},
        ]

        donnee: Donnee = next(
            (
                d
                for d in donnees
                if d.type_name
                == (
                    champ["__typename"] + "Descriptor"
                    if not str(champ["__typename"]).endswith("NumberChamp")
                    else "NumberChampDescriptor"
                )
                and d.label == champ["label"]
            ),
            None,
        )
        if donnee is not None:
            # Récupération des données additionnelles en fonction du type du champ
            additional_data = {}
            for mapping in _mappingTypes:
                if champ["__typename"] in mapping["types"]:
                    for field in mapping["fields"]:
                        additional_data[field] = champ[field]

            # Création de la valeur en BDD
            valeur = ValeurDonnee(
                **{
                    "dossier_number": dossier_number,
                    "donnee_id": donnee.id,
                    "valeur": champ["stringValue"],
                    "additional_data": additional_data,
                }
            )
            db.session.add(valeur)
            db.session.flush()
            return valeur
