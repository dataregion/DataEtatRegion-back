CREATE MATERIALIZED VIEW vt_flatten_summarized_ademe AS
 SELECT 'ADEME'::text AS source,
    fa.id,
    fa.annee,
    fa.montant_ae,
    fa.montant_cp,
    'ADEME'::text AS code_programme,
    fa.beneficiaire_code AS siret,
    fa.beneficiaire_commune_code AS code_commune,
    fa."beneficiaire_commune_codeDepartement" AS code_departement,
    fa."beneficiaire_commune_codeCrte" AS code_crte,
    fa."beneficiaire_commune_codeEpci" AS code_epci,
    fa.beneficiaire_qpv_code AS code_qpv,
    fa.beneficiaire_qpv24_code AS code_qpv24,
    fa."beneficiaire_categorieJuridique_type" AS categorie_juridique,
    NULL::text AS loc_inter,
    NULL::text AS code_departement_loc_inter,
    NULL::text AS code_commune_loc_inter,
    NULL::text AS code_epci_loc_inter,
    NULL::text AS code_crte_loc_inter,
    NULL::text AS lieu_action_code_qpv
   FROM flatten_ademe fa
  WHERE fa.beneficiaire_commune_code IS NOT NULL
  ORDER BY 'ADEME'::text, fa.id;