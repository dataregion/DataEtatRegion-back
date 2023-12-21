CREATE VIEW flatten_ae AS
SELECT
       'FINANCIAL_DATA_AE' as source, -- Raccord avec l'enum DataType
       root.id as id,
       root.n_poste_ej,
       root.n_ej,
       root.annee as annee,
       root.contrat_etat_region,
       root.compte_budgetaire,
       aggr_mt_ae.montant_ae,
       aggr_mt_cp.montant_cp,
       aggr_mt_cp.date_dernier_paiement as "dateDeDernierPaiement",
       root.date_replication as "dateDeCreation",
    -- domaine fonctionnel
       rdf.code as "domaineFonctionnel_code",
       rdf.label as "domaineFonctionnel_label",
    -- referentiel programmation
       rp.code as "referentielProgrammation_code",
       rp.label as "referentielProgrammation_label",
    -- groupe de marchandise
       rgm.code as "groupeMarchandise_code",
       rgm.label as "groupeMarchandise_label",
    -- programme
       rcp.code as "programme_code",
       rcp.label as "programme_label",
       rcp_rt."label" as "programme_theme",
    -- beneficiaire
       rs.code as "beneficiaire_code",
       rs.denomination as "beneficiaire_denomination",
       rs_rcj.type as "beneficiaire_categorieJuridique_type",
       rs_rqpv.code as "beneficiaire_qpv_code",
       rs_rqpv.label as "beneficiaire_qpv_label",
       -- commune du beneficiaire
       rs_rc.code as "beneficiaire_commune_code",
       rs_rc.label_commune as "beneficiaire_commune_label",
       rs_rc.code_region as "beneficiaire_commune_codeRegion",
       rs_rc.label_region as "beneficiaire_commune_labelRegion",
       rs_rc.code_departement as "beneficiaire_commune_codeDepartement",
       rs_rc.label_departement as "beneficiaire_commune_labelDepartement",
       rs_rc.code_epci as "beneficiaire_commune_codeEpci",
       rs_rc.label_epci as "beneficiaire_commune_labelEpci",
       rs_rc.code_crte as "beneficiaire_commune_codeCrte",
       rs_rc.label_crte as "beneficiaire_commune_labelCrte",
       rs_rc_ra.code as "beneficiaire_commune_arrondissement_code",
       rs_rc_ra.label as "beneficiaire_commune_arrondissement_label",
    -- localisation interministerielle
      rli.code as "localisationInterministerielle_code",
      rli.label as "localisationInterministerielle_label",
      substring(rli.code,4,2) as "localisationInterministerielle_codeDepartement",
      -- commune de la localisation interministerielle
      rli_rc.code as "localisationInterministerielle_commune_code",
      rli_rc.label_commune as "localisationInterministerielle_commune_label",
      rli_rc.code_region as "localisationInterministerielle_commune_codeRegion",
      rli_rc.label_region as "localisationInterministerielle_commune_labelRegion",
      rli_rc.code_departement as "localisationInterministerielle_commune_codeDepartement",
      rli_rc.label_departement as "localisationInterministerielle_commune_labelDepartement",
      rli_rc.code_epci as "localisationInterministerielle_commune_codeEpci",
      rli_rc.label_epci as "localisationInterministerielle_commune_labelEpci",
      rli_rc.code_crte as "localisationInterministerielle_commune_codeCrte",
      rli_rc.label_crte as "localisationInterministerielle_commune_labelCrte",
      rli_rc_ra.code as "localisationInterministerielle_commune_arrondissement_code",
      rli_rc_ra.label as "localisationInterministerielle_commune_arrondissement_label",
    -- source region
      root.source_region as source_region,
    -- update/creation date
      root.updated_at as updated_at,
      root.created_at as created_at
   FROM "financial_ae" root
   -- siret => beneficiaire
   LEFT JOIN ref_siret rs ON root.siret = rs.code
   LEFT JOIN ref_categorie_juridique rs_rcj ON rs.categorie_juridique = rs_rcj.code
   LEFT JOIN ref_qpv rs_rqpv ON rs.code_qpv = rs_rqpv.code
   LEFT JOIN ref_commune rs_rc ON rs.code_commune = rs_rc.code
   LEFT JOIN ref_arrondissement rs_rc_ra ON rs_rc.code_arrondissement = rs_rc_ra.code 
   -- Localisation interministerielle
   LEFT JOIN ref_localisation_interministerielle rli on rli.code = root.localisation_interministerielle
   LEFT JOIN ref_commune rli_rc on rli_rc.id = rli.commune_id
   LEFT JOIN ref_arrondissement rli_rc_ra on rli_rc.code_arrondissement = rli_rc_ra.code
   -- Domaine fonctionnel
   LEFT JOIN ref_domaine_fonctionnel rdf on rdf.code = root.domaine_fonctionnel
   -- Code programme
   LEFT JOIN ref_code_programme rcp on rcp.code = root.programme
   LEFT JOIN ref_theme rcp_rt on rcp_rt.id = rcp.theme
   -- Programmation
   LEFT JOIN ref_programmation rp on rp.code = root.referentiel_programmation
   LEFT JOIN ref_groupe_marchandise rgm on root.groupe_marchandise = rgm.code
   -- Aggregations
   LEFT JOIN (
       select
         root.id as id,
         SUM(mce.montant) as montant_ae
       FROM "financial_ae" root
       LEFT JOIN montant_financial_ae mce ON root.id = mce.id_financial_ae
       GROUP BY root.id
   ) aggr_mt_ae on aggr_mt_ae.id = root.id
   LEFT JOIN (
       select
         root.id as id,
         SUM(fcp.montant) as montant_cp,
         max(fcp.date_derniere_operation_dp) as date_dernier_paiement
       FROM "financial_ae" root
       LEFT JOIN financial_cp fcp ON fcp.id_ae = root.id
       GROUP BY root.id
   ) aggr_mt_cp on aggr_mt_cp.id = root.id
;