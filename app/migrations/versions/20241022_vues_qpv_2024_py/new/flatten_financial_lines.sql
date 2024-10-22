CREATE OR REPLACE VIEW public._flatten_financial_lines
    AS SELECT flatten_ae.source,
      flatten_ae.id,
      flatten_ae.n_poste_ej,
      flatten_ae.n_ej,
      flatten_ae.annee,
      flatten_ae.contrat_etat_region,
      flatten_ae.compte_budgetaire,
      flatten_ae.montant_ae,
      flatten_ae.montant_cp,
      flatten_ae."dateDeDernierPaiement",
      flatten_ae."dateDeCreation",
      flatten_ae."domaineFonctionnel_code",
      flatten_ae."domaineFonctionnel_label",
      flatten_ae."referentielProgrammation_code",
      flatten_ae."referentielProgrammation_label",
      flatten_ae."groupeMarchandise_code",
      flatten_ae."groupeMarchandise_label",
      flatten_ae.programme_code,
      flatten_ae.programme_label,
      flatten_ae.programme_theme,
      flatten_ae.beneficiaire_code,
      flatten_ae.beneficiaire_denomination,
      flatten_ae."beneficiaire_categorieJuridique_type",
      flatten_ae.beneficiaire_qpv_code,
      flatten_ae.beneficiaire_qpv_label,
      flatten_ae.beneficiaire_qpv24_code,
      flatten_ae.beneficiaire_qpv24_label,
      flatten_ae.beneficiaire_commune_code,
      flatten_ae.beneficiaire_commune_label,
      flatten_ae."beneficiaire_commune_codeRegion",
      flatten_ae."beneficiaire_commune_labelRegion",
      flatten_ae."beneficiaire_commune_codeDepartement",
      flatten_ae."beneficiaire_commune_labelDepartement",
      flatten_ae."beneficiaire_commune_codeEpci",
      flatten_ae."beneficiaire_commune_labelEpci",
      flatten_ae."beneficiaire_commune_codeCrte",
      flatten_ae."beneficiaire_commune_labelCrte",
      flatten_ae.beneficiaire_commune_arrondissement_code,
      flatten_ae.beneficiaire_commune_arrondissement_label,
      flatten_ae."localisationInterministerielle_code",
      flatten_ae."localisationInterministerielle_label",
      flatten_ae."localisationInterministerielle_codeDepartement",
      flatten_ae."localisationInterministerielle_commune_code",
      flatten_ae."localisationInterministerielle_commune_label",
      flatten_ae."localisationInterministerielle_commune_codeRegion",
      flatten_ae."localisationInterministerielle_commune_labelRegion",
      flatten_ae."localisationInterministerielle_commune_codeDepartement",
      flatten_ae."localisationInterministerielle_commune_labelDepartement",
      flatten_ae."localisationInterministerielle_commune_codeEpci",
      flatten_ae."localisationInterministerielle_commune_labelEpci",
      flatten_ae."localisationInterministerielle_commune_codeCrte",
      flatten_ae."localisationInterministerielle_commune_labelCrte",
      flatten_ae."localisationInterministerielle_commune_arrondissement_code",
      flatten_ae."localisationInterministerielle_commune_arrondissement_label",
      flatten_ae.source_region,
      flatten_ae.updated_at,
      flatten_ae.created_at,
      flatten_ae."centreCouts_code",
      flatten_ae."centreCouts_label",
      flatten_ae."centreCouts_description",
      flatten_ae.data_source
      FROM flatten_ae
   UNION ALL
   SELECT flatten_ademe.source,
      flatten_ademe.id,
      flatten_ademe.n_poste_ej,
      flatten_ademe.n_ej,
      flatten_ademe.annee,
      flatten_ademe.contrat_etat_region,
      flatten_ademe.compte_budgetaire,
      flatten_ademe.montant_ae,
      flatten_ademe.montant_cp,
      flatten_ademe."dateDeDernierPaiement",
      flatten_ademe."dateDeCreation",
      flatten_ademe."domaineFonctionnel_code",
      flatten_ademe."domaineFonctionnel_label",
      flatten_ademe."referentielProgrammation_code",
      flatten_ademe."referentielProgrammation_label",
      flatten_ademe."groupeMarchandise_code",
      flatten_ademe."groupeMarchandise_label",
      flatten_ademe.programme_code,
      flatten_ademe.programme_label,
      flatten_ademe.programme_theme,
      flatten_ademe.beneficiaire_code,
      flatten_ademe.beneficiaire_denomination,
      flatten_ademe."beneficiaire_categorieJuridique_type",
      flatten_ademe.beneficiaire_qpv_code,
      flatten_ademe.beneficiaire_qpv_label,
      flatten_ademe.beneficiaire_qpv24_code,
      flatten_ademe.beneficiaire_qpv24_label,
      flatten_ademe.beneficiaire_commune_code,
      flatten_ademe.beneficiaire_commune_label,
      flatten_ademe."beneficiaire_commune_codeRegion",
      flatten_ademe."beneficiaire_commune_labelRegion",
      flatten_ademe."beneficiaire_commune_codeDepartement",
      flatten_ademe."beneficiaire_commune_labelDepartement",
      flatten_ademe."beneficiaire_commune_codeEpci",
      flatten_ademe."beneficiaire_commune_labelEpci",
      flatten_ademe."beneficiaire_commune_codeCrte",
      flatten_ademe."beneficiaire_commune_labelCrte",
      flatten_ademe.beneficiaire_commune_arrondissement_code,
      flatten_ademe.beneficiaire_commune_arrondissement_label,
      flatten_ademe."localisationInterministerielle_code",
      flatten_ademe."localisationInterministerielle_label",
      flatten_ademe."localisationInterministerielle_codeDepartement",
      flatten_ademe."localisationInterministerielle_commune_code",
      flatten_ademe."localisationInterministerielle_commune_label",
      flatten_ademe."localisationInterministerielle_commune_codeRegion",
      flatten_ademe."localisationInterministerielle_commune_labelRegion",
      flatten_ademe."localisationInterministerielle_commune_codeDepartement",
      flatten_ademe."localisationInterministerielle_commune_labelDepartement",
      flatten_ademe."localisationInterministerielle_commune_codeEpci",
      flatten_ademe."localisationInterministerielle_commune_labelEpci",
      flatten_ademe."localisationInterministerielle_commune_codeCrte",
      flatten_ademe."localisationInterministerielle_commune_labelCrte",
      flatten_ademe."localisationInterministerielle_commune_arrondissement_code",
      flatten_ademe."localisationInterministerielle_commune_arrondissement_label",
      flatten_ademe.source_region,
      flatten_ademe.updated_at,
      flatten_ademe.created_at,
      flatten_ademe."centreCouts_code",
      flatten_ademe."centreCouts_label",
      flatten_ademe."centreCouts_description",
      flatten_ademe.data_source
      FROM flatten_ademe
   UNION ALL
   SELECT flatten_orphan_cp.source,
      flatten_orphan_cp.id,
      flatten_orphan_cp.n_poste_ej,
      flatten_orphan_cp.n_ej,
      flatten_orphan_cp.annee,
      flatten_orphan_cp.contrat_etat_region,
      flatten_orphan_cp.compte_budgetaire,
      flatten_orphan_cp.montant_ae,
      flatten_orphan_cp.montant_cp,
      flatten_orphan_cp."dateDeDernierPaiement",
      flatten_orphan_cp."dateDeCreation",
      flatten_orphan_cp."domaineFonctionnel_code",
      flatten_orphan_cp."domaineFonctionnel_label",
      flatten_orphan_cp."referentielProgrammation_code",
      flatten_orphan_cp."referentielProgrammation_label",
      flatten_orphan_cp."groupeMarchandise_code",
      flatten_orphan_cp."groupeMarchandise_label",
      flatten_orphan_cp.programme_code,
      flatten_orphan_cp.programme_label,
      flatten_orphan_cp.programme_theme,
      flatten_orphan_cp.beneficiaire_code,
      flatten_orphan_cp.beneficiaire_denomination,
      flatten_orphan_cp."beneficiaire_categorieJuridique_type",
      flatten_orphan_cp.beneficiaire_qpv_code,
      flatten_orphan_cp.beneficiaire_qpv_label,
      flatten_orphan_cp.beneficiaire_qpv24_code,
      flatten_orphan_cp.beneficiaire_qpv24_label,
      flatten_orphan_cp.beneficiaire_commune_code,
      flatten_orphan_cp.beneficiaire_commune_label,
      flatten_orphan_cp."beneficiaire_commune_codeRegion",
      flatten_orphan_cp."beneficiaire_commune_labelRegion",
      flatten_orphan_cp."beneficiaire_commune_codeDepartement",
      flatten_orphan_cp."beneficiaire_commune_labelDepartement",
      flatten_orphan_cp."beneficiaire_commune_codeEpci",
      flatten_orphan_cp."beneficiaire_commune_labelEpci",
      flatten_orphan_cp."beneficiaire_commune_codeCrte",
      flatten_orphan_cp."beneficiaire_commune_labelCrte",
      flatten_orphan_cp.beneficiaire_commune_arrondissement_code,
      flatten_orphan_cp.beneficiaire_commune_arrondissement_label,
      flatten_orphan_cp."localisationInterministerielle_code",
      flatten_orphan_cp."localisationInterministerielle_label",
      flatten_orphan_cp."localisationInterministerielle_codeDepartement",
      flatten_orphan_cp."localisationInterministerielle_commune_code",
      flatten_orphan_cp."localisationInterministerielle_commune_label",
      flatten_orphan_cp."localisationInterministerielle_commune_codeRegion",
      flatten_orphan_cp."localisationInterministerielle_commune_labelRegion",
      flatten_orphan_cp."localisationInterministerielle_commune_codeDepartement",
      flatten_orphan_cp."localisationInterministerielle_commune_labelDepartement",
      flatten_orphan_cp."localisationInterministerielle_commune_codeEpci",
      flatten_orphan_cp."localisationInterministerielle_commune_labelEpci",
      flatten_orphan_cp."localisationInterministerielle_commune_codeCrte",
      flatten_orphan_cp."localisationInterministerielle_commune_labelCrte",
      flatten_orphan_cp."localisationInterministerielle_commune_arrondissement_code",
      flatten_orphan_cp."localisationInterministerielle_commune_arrondissement_label",
      flatten_orphan_cp.source_region,
      flatten_orphan_cp.updated_at,
      flatten_orphan_cp.created_at,
      flatten_orphan_cp."centreCouts_code",
      flatten_orphan_cp."centreCouts_label",
      flatten_orphan_cp."centreCouts_description",
      flatten_orphan_cp.data_source
      FROM flatten_orphan_cp;