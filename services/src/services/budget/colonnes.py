from models.entities.financial.query.FlattenFinancialLines import (
    EnrichedFlattenFinancialLines,
)

from models.value_objects.colonne import Colonne


def get_list_colonnes_tableau() -> list[Colonne]:
    return [
        Colonne(
            code=EnrichedFlattenFinancialLines.source.description,
            label="Source de données",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.id.description, label="ID", type=int
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.n_ej.description, label="N° EJ", type=str
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.n_poste_ej.description,
            label="N° Poste EJ",
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.montant_ae.description,
            label="Montant engagé",
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.montant_cp.description,
            label="Montant payé",
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_theme.description,
            label="Thème",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_code.description,
            label="Code programme",
            concatenate=EnrichedFlattenFinancialLines.programme_label.description,
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_label.description,
            label="Programme",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.domaineFonctionnel_code.description,
            label="Code domaine fonctionnel",
            concatenate=EnrichedFlattenFinancialLines.domaineFonctionnel_label.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.domaineFonctionnel_label.description,
            label="Domaine fonctionnel",
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.referentielProgrammation_code.description,
            label="Code Ref Programmation",
            concatenate=EnrichedFlattenFinancialLines.referentielProgrammation_label.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.referentielProgrammation_label.description,
            label="Ref Programmation",
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_code.description,
            label="Code Commune du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_label.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_label.description,
            label="Commune du SIRET",
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeCrte.description,
            label="Code CRTE du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelCrte.description,
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelCrte.description,
            label="CRTE du SIRET",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeEpci.description,
            label="Code EPCI du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelEpci.description,
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelEpci.description,
            label="EPCI du SIRET",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_arrondissement_code.description,
            label="Code Arrondissement du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_arrondissement_label.description,
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_arrondissement_label.description,
            label="Arrondissement du SIRET",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeDepartement.description,
            label="Code Département du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelDepartement.description,
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelDepartement.description,
            label="Département du SIRET",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeRegion.description,
            label="Code Région du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelRegion.description,
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelRegion.description,
            label="Région du SIRET",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.localisationInterministerielle_code.description,
            label="Code localisation interministérielle",
            concatenate=EnrichedFlattenFinancialLines.localisationInterministerielle_label.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.localisationInterministerielle_label.description,
            label="Localisation interministérielle",
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.compte_budgetaire.description,
            label="Compte budgétaire",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.contrat_etat_region.description,
            label="CPER",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.groupeMarchandise_code.description,
            label="Code groupe marchandise",
            concatenate=EnrichedFlattenFinancialLines.groupeMarchandise_label.description,
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.groupeMarchandise_label.description,
            label="Groupe marchandise",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_code.description,
            label="SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_denomination.description,
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_denomination.description,
            label="Bénéficiaire",
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_categorieJuridique_type.description,
            label="Type d'établissement",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_qpv_code.description,
            label="Code QPV",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_qpv_label.description,
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_qpv_label.description,
            label="QPV",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.dateDeDernierPaiement.description,
            label="Date dernier paiement",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.dateDeCreation.description,
            label="Date création EJ",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.annee.description,
            label="Année Exercice comptable",
            type=int,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.centreCouts_code.description,
            label="Code centre coûts",
            concatenate=EnrichedFlattenFinancialLines.centreCouts_label.description,
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.centreCouts_label.description,
            label="Label centre coûts",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.centreCouts_description.description,
            label="Centre coûts",
            default=False,
            type=str,
        ),
        Colonne(code=EnrichedFlattenFinancialLines.tags.key, label="Tags", type=list),
        Colonne(
            code=EnrichedFlattenFinancialLines.source_region.description,
            label="Source Région",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.data_source.description,
            label="Source Chorus",
            default=False,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.date_modification.description,
            label="Date modification EJ",
            default=False,
            type=str,
        ),
    ]


def get_list_colonnes_grouping() -> list[Colonne]:
    return [
        Colonne(
            code=EnrichedFlattenFinancialLines.annee.description,
            label="Année exercie comptable",
            type=int,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeRegion.description,
            label="Code Région du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelRegion.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeDepartement.description,
            label="Code Département du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelDepartement.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeCrte.description,
            label="Code CRTE du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelCrte.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_codeEpci.description,
            label="Code EPCI du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_labelEpci.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_commune_code.description,
            label="Code Commune du SIRET",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_commune_label.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_qpv_code.description,
            label="Code QPV",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_qpv_label.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.localisationInterministerielle_code.description,
            label="Code Localisation interministérielle",
            concatenate=EnrichedFlattenFinancialLines.localisationInterministerielle_label.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_theme.description,
            label="Thème",
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.programme_code.description,
            label="Programme",
            concatenate=EnrichedFlattenFinancialLines.programme_label.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.domaineFonctionnel_code.description,
            label="Domaine fonctionnel",
            concatenate=EnrichedFlattenFinancialLines.domaineFonctionnel_label.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.referentielProgrammation_code.description,
            label="Ref Programmation",
            concatenate=EnrichedFlattenFinancialLines.referentielProgrammation_label.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.centreCouts_code.description,
            label="Centre coûts",
            concatenate=EnrichedFlattenFinancialLines.centreCouts_label.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_code.description,
            label="Bénéficiaire",
            concatenate=EnrichedFlattenFinancialLines.beneficiaire_denomination.description,
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.beneficiaire_categorieJuridique_type.description,
            label="Type d'établissement",
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.compte_budgetaire.description,
            label="Compte budgétaire",
            type=str,
        ),
        Colonne(
            code=EnrichedFlattenFinancialLines.groupeMarchandise_code.description,
            label="Groupe marchandise",
            concatenate=EnrichedFlattenFinancialLines.groupeMarchandise_label.description,
            type=str,
        ),
        Colonne(code=EnrichedFlattenFinancialLines.tags.key, label="Tags", type=list),
    ]
