from sqlalchemy import (
    Column,
    func,
    literal,
    or_,
)
from sqlalchemy.orm.session import Session

from models.entities.common.Tags import Tags
from models.entities.financial.query.FlattenFinancialLines import (
    EnrichedFlattenFinancialLines as FinancialLines,
)
from models.value_objects.common import TypeCodeGeo
from models.value_objects.tags import TagVO
from services.helper import (
    TypeCodeGeoToFinancialLineLocInterministerielleCodeGeoResolver,
)
from services.helper import TypeCodeGeoToFinancialLineBeneficiaireCodeGeoResolver

from apis.apps.budget.models.budget_query_params import BudgetQueryParams
from apis.shared.colonne import Colonne
from apis.shared.enums import BenefOrLoc
from apis.shared.query_builder import FinancialLineQueryBuilder


class BudgetQueryBuilder(FinancialLineQueryBuilder):
    """
    Constructeur de requête SQLAlchemy pour la vue budget
    """

    def __init__(self, session: Session, params: BudgetQueryParams) -> None:
        super().__init__(FinancialLines, session, params)

        self.__init_resolvers__()
        self.__init_mechanisme_grouping__(params)

    def __init_resolvers__(self):
        self._code_geo_column_locinterministerielle_resolver = (
            TypeCodeGeoToFinancialLineLocInterministerielleCodeGeoResolver()
        )
        self._code_geo_column_benef_resolver = TypeCodeGeoToFinancialLineBeneficiaireCodeGeoResolver()

    def __init_mechanisme_grouping__(self, params: BudgetQueryParams):
        self.groupby_colonne = None
        self.dynamic_conditions = None

        if params.grouping is not None:
            self.groupby_colonne, self.dynamic_conditions = self._rec_grouping_mechanisme(
                params.grouping, params.grouped, {}
            )
            if self.groupby_colonne is None:
                return

            if params.grouped is None or len(params.grouped) < len(params.grouping):
                assert isinstance(self.groupby_colonne.code, str)  # type: ignore
                colonnes = [
                    getattr(FinancialLines, self.groupby_colonne.code).label("value"),  # type: ignore
                    func.coalesce(func.count(FinancialLines.id), 0).label("total"),
                    func.coalesce(func.sum(FinancialLines.montant_ae), 0).label("total_montant_engage"),
                    func.coalesce(func.sum(FinancialLines.montant_cp), 0).label("total_montant_paye"),
                ]
                if self.groupby_colonne.concatenate:
                    colonnes.append(
                        func.concat(
                            getattr(FinancialLines, self.groupby_colonne.code),
                            literal(" - "),
                            getattr(FinancialLines, self.groupby_colonne.concatenate),
                        ).label("label")
                    )
                else:
                    colonnes.append(getattr(FinancialLines, self.groupby_colonne.code).label("label"))
                self.select_custom_model_properties(colonnes, is_grouping=True)

    def _rec_grouping_mechanisme(
        self,
        grouping: list[Colonne],
        grouped: list[str] | None,
        conditions: dict,
    ) -> tuple[Colonne | None, dict]:
        if grouped is None or len(grouped) == 0:
            colonne = grouping[0] if len(grouping) > 0 else None
            return colonne, conditions

        conditions[grouping[0].code] = {"value": grouped[0] if grouped[0] != "None" else None}
        if grouping[0].type is not None:
            conditions[grouping[0].code]["type"] = grouping[0].type

        return self._rec_grouping_mechanisme(grouping[1:], grouped[1:], conditions)

    """
    Méthodes de conditions spécifiques aux requêtes de Budget
    """

    def niveau_code_geo_in(self, niveau_geo: str | None, code_geo: list | None, source_region: str):
        if niveau_geo is not None and code_geo is not None:
            self.where_geo(TypeCodeGeo[niveau_geo.upper()], code_geo, source_region)
        return self

    def tags_fullname_in(self, fullnames: list[str] | None):
        if fullnames is not None:
            _tags = map(TagVO.sanitize_str, fullnames)
            fullnamein = Tags.fullname.in_(_tags)
            self.where_custom(FinancialLines.tags.any(fullnamein))

        return self

    def where_geo(
        self,
        type_geo: TypeCodeGeo,
        list_code_geo: list[str],
        source_region: str,
        benef_or_loc: BenefOrLoc | None = None,
    ):
        if list_code_geo is None:
            return self

        column_codegeo_commune_loc_inter = self._code_geo_column_locinterministerielle_resolver.code_geo_column(
            type_geo
        )
        column_codegeo_commune_beneficiaire = self._code_geo_column_benef_resolver.code_geo_column(type_geo)

        self._where_geo(
            type_geo,
            list_code_geo,
            source_region,
            column_codegeo_commune_loc_inter,
            column_codegeo_commune_beneficiaire,
            benef_or_loc,
        )
        return self

    def _where_geo(
        self,
        type_geo: TypeCodeGeo,
        list_code_geo: list[str],
        source_region: str,
        column_codegeo_commune_loc_inter: Column[str] | None,
        column_codegeo_commune_beneficiaire: Column[str] | None,
        benef_or_loc: BenefOrLoc | None = None,
    ):
        conds = []

        #
        # On calcule les patterns valides pour les codes de localisations interministerielles
        #
        if benef_or_loc is None or benef_or_loc is BenefOrLoc.LOCALISATION_INTER:
            # Calcule les codes de la localisation interministerielle suivant le code geographique
            code_locinter_pattern = []
            if type_geo is TypeCodeGeo.REGION:
                code_locinter_pattern = [f"N{code}" for code in list_code_geo]
            elif type_geo is TypeCodeGeo.DEPARTEMENT:
                code_locinter_pattern = [f"N{source_region}{code}" for code in list_code_geo]
            # fmt:off
            _conds_code_locinter = [
                FinancialLines.localisationInterministerielle_code.ilike(f"{pattern}%")
                for pattern
                in code_locinter_pattern
            ]
            # fmt:on
            if len(code_locinter_pattern) > 0:
                conds.append(or_(*_conds_code_locinter))

        #
        # Ou les code geo de la commune associée à la localisation interministerielle
        #
        if column_codegeo_commune_loc_inter is not None and (
            benef_or_loc is None or benef_or_loc == BenefOrLoc.LOCALISATION_INTER
        ):
            conds.append(column_codegeo_commune_loc_inter.in_(list_code_geo))

        #
        # Ou les code geo de la commune associée au bénéficiaire
        #
        if column_codegeo_commune_beneficiaire is not None and (
            benef_or_loc is None
            or benef_or_loc == BenefOrLoc.BENEFICIAIRE
            or benef_or_loc == BenefOrLoc.LOCALISATION_QPV
        ):
            conds.append(column_codegeo_commune_beneficiaire.in_(list_code_geo))

        where_clause = or_(*conds)
        self._query = self._query.where(where_clause)
        return self._query
