from models.entities.financial.query.FlattenFinancialLines import EnrichedFlattenFinancialLines

from apis.apps.budget.models.colonne import Colonne


def get_list_colonnes_tableau() -> list[Colonne]:
    return [
        Colonne(code=EnrichedFlattenFinancialLines.source.description, label="Source de données"),
        Colonne(code=EnrichedFlattenFinancialLines.n_ej.description, label="N° EJ"),
        Colonne(code=EnrichedFlattenFinancialLines.n_poste_ej.description, label="N° Poste EJ"),
        Colonne(code=EnrichedFlattenFinancialLines.montant_ae.description, label="Montant engagé"),
        Colonne(code=EnrichedFlattenFinancialLines.montant_cp.description, label="Montant payé"),
        Colonne(code=EnrichedFlattenFinancialLines.programme_theme.description, label="Thème"),
        Colonne(code=EnrichedFlattenFinancialLines.programme_code.description, label="Code programme"),
        Colonne(code=EnrichedFlattenFinancialLines.programme_label.description, label="Programme"),
        Colonne(code=EnrichedFlattenFinancialLines.domaineFonctionnel_code.description, label="Code domaine fonctionnel"),
        Colonne(code=EnrichedFlattenFinancialLines.domaineFonctionnel_label.description, label="Domaine fonctionnel"),
        Colonne(code=EnrichedFlattenFinancialLines.referentielProgrammation_label.description, label="Ref Programmation"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_label, label="Commune du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelCrte.description, label="CRTE du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelEpci.description, label="EPCI du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_arrondissement_label.description, label="Arrondissement du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelDepartement.description, label="Département du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelRegion.description, label="Région du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.localisationInterministerielle_code.description, label="Code localisation interministérielle"),
        Colonne(code=EnrichedFlattenFinancialLines.localisationInterministerielle_label.description, label="Localisation interministérielle"),
        Colonne(code=EnrichedFlattenFinancialLines.compte_budgetaire.description, label="Compte budgétaire"),
        Colonne(code=EnrichedFlattenFinancialLines.contrat_etat_region.description, label="CPER"),
        Colonne(code=EnrichedFlattenFinancialLines.groupeMarchandise_code.description, label="Code groupe marchandise"),
        Colonne(code=EnrichedFlattenFinancialLines.groupeMarchandise_label.description, label="Groupe marchandise"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_code.description, label="SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_denomination.description, label="Bénéficiaire"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_categorieJuridique_type.description, label="Type d'établissement"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_qpv_code.description, label="Code QPV"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_qpv_label.description, label="QPV"),
        Colonne(code=EnrichedFlattenFinancialLines.dateDeDernierPaiement.description, label="Date dernier paiement"),
        Colonne(code=EnrichedFlattenFinancialLines.dateDeCreation.description, label="Date création EJ"),
        Colonne(code=EnrichedFlattenFinancialLines.annee.description, label="Année Exercice comptable", type=int),
        Colonne(code=EnrichedFlattenFinancialLines.centreCouts_code.description, label="Code centre coûts"),
        Colonne(code=EnrichedFlattenFinancialLines.centreCouts_label.description, label="Label centre coûts"),
        Colonne(code=EnrichedFlattenFinancialLines.centreCouts_description.description, label="Centre coûts"),
        Colonne(code=EnrichedFlattenFinancialLines.tags.key, label="Tags"),
        Colonne(code=EnrichedFlattenFinancialLines.data_source.description, label="Source Chorus"),
        Colonne(code=EnrichedFlattenFinancialLines.date_modification.description, label="Date modification EJ")
    ]


def get_list_colonnes_grouping() -> list[Colonne]:
    return [
        Colonne(code=EnrichedFlattenFinancialLines.annee.description, label="Année exercie comptable", type=int),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelRegion.description, label="Région du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelDepartement.description, label="Département du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelCrte.description, label="CRTE du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_labelEpci.description, label="EPCI du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_commune_label.description, label="Commune du SIRET"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_qpv_label.description, label="Code QPV"),
        Colonne(code=EnrichedFlattenFinancialLines.localisationInterministerielle_label.description, label="Localisation interministérielle"),
        Colonne(code=EnrichedFlattenFinancialLines.programme_theme.description, label="Thème"),
        Colonne(code=EnrichedFlattenFinancialLines.programme_code.description, label="Programme"),
        Colonne(code=EnrichedFlattenFinancialLines.domaineFonctionnel_label.description, label="Domaine fonctionnel"),
        Colonne(code=EnrichedFlattenFinancialLines.referentielProgrammation_label.description, label="Ref Programmation"),
        Colonne(code=EnrichedFlattenFinancialLines.centreCouts_description.description, label="Centre coûts"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_denomination.description, label="Bénéficiaire"),
        Colonne(code=EnrichedFlattenFinancialLines.beneficiaire_categorieJuridique_type.description, label="Type d'établissement"),
        Colonne(code=EnrichedFlattenFinancialLines.compte_budgetaire.description, label="Compte budgétaire"),
        Colonne(code=EnrichedFlattenFinancialLines.groupeMarchandise_label.description, label="Groupe marchandise"),
        Colonne(code=EnrichedFlattenFinancialLines.tags.key, label="Tags")
    ]
