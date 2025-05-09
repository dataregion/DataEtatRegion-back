CREATE MATERIALIZED VIEW vt_flatten_summarized_ae AS
 SELECT 'FINANCIAL_DATA_AE'::text AS source,
    fa.id,
    fa.n_poste_ej,
    fa.n_ej,
    fa.source_region,
    fa.annee,
    fa.contrat_etat_region,
    fa.montant_ae,
    fa.montant_cp,
    fa."dateDeDernierPaiement" AS date_dernier_paiement,
    fa."domaineFonctionnel_code" AS code_domaine_fonctionnel,
    fa."domaineFonctionnel_label" AS label_domaine_fonctionnel,
    fa.programme_theme AS theme,
    fa.programme_code AS code_programme,
    fa.programme_label AS label_programme,
    fa."referentielProgrammation_code" AS ref_programmation,
    fa."referentielProgrammation_label" AS label_ref_programmation,
    fa.beneficiaire_code AS siret,
    fa.beneficiaire_denomination AS denomination,
    fa.beneficiaire_commune_code AS code_commune,
    fa."beneficiaire_commune_codeDepartement" AS code_departement,
    fa."beneficiaire_commune_codeCrte" AS code_crte,
    fa."beneficiaire_commune_codeEpci" AS code_epci,
    fa.beneficiaire_qpv_code AS code_qpv,
    fa.beneficiaire_qpv24_code AS code_qpv24,
    fa."beneficiaire_categorieJuridique_type" AS categorie_juridique,
    fa."localisationInterministerielle_code" AS loc_inter,
    fa."localisationInterministerielle_label" AS label_loc_inter,
    fa."localisationInterministerielle_codeDepartement" AS code_departement_loc_inter,
    fa."localisationInterministerielle_commune_code" AS code_commune_loc_inter,
    fa."localisationInterministerielle_commune_codeEpci" AS code_epci_loc_inter,
    fa."localisationInterministerielle_commune_codeCrte" AS code_crte_loc_inter,
    fa.lieu_action_code_qpv AS lieu_action_code_qpv
   FROM flatten_ae fa
  WHERE fa.beneficiaire_commune_code IS NOT NULL
  ORDER BY 'FINANCIAL_DATA_AE'::text, fa.id, fa.n_ej, fa.n_poste_ej, fa.source_region, fa.annee;