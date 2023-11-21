CREATE MATERIALIZED VIEW flatten_ademe AS
SELECT
       'ADEME' as source, -- Raccord avec l'enum DataType
       root.id as id,
       NULL::int4 AS n_poste_ej,
       NULL AS n_ej,
       date_part('year', root.date_convention) AS annee,
       NULL AS contrat_etat_region,
       NULL AS compte_budgetaire,
       root.montant as montant_ae,
       root.montant as montant_cp,
       CAST(NULL AS TIMESTAMP) as "dateDeDernierPaiement",
       CAST(NULL AS TIMESTAMP) as "dateDeCreation",
    -- domaine fonctionnel
       NULL as "domaineFonctionnel_code",
       NULL as "domaineFonctionnel_label",
    -- referentiel programmation
       NULL as "referentielProgrammation_code",
       NULL as "referentielProgrammation_label",
    -- groupe de marchandise
       NULL as "groupeMarchandise_code",
       NULL as "groupeMarchandise_label",
    -- programme
       'ADEME' as "programme_code",
       NULL as "programme_label",
       NULL as "programme_theme",
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
      NULL as "localisationInterministerielle_code",
      NULL as "localisationInterministerielle_label",
      NULL as "localisationInterministerielle_codeDepartement",
      -- commune de la localisation interministerielle
      NULL as "localisationInterministerielle_commune_code",
      NULL as "localisationInterministerielle_commune_label",
      NULL as "localisationInterministerielle_commune_codeRegion",
      NULL as "localisationInterministerielle_commune_labelRegion",
      NULL as "localisationInterministerielle_commune_codeDepartement",
      NULL as "localisationInterministerielle_commune_labelDepartement",
      NULL as "localisationInterministerielle_commune_codeEpci",
      NULL as "localisationInterministerielle_commune_labelEpci",
      NULL as "localisationInterministerielle_commune_codeCrte",
      NULL as "localisationInterministerielle_commune_labelCrte",
      NULL as "localisationInterministerielle_commune_arrondissement_code",
      NULL as "localisationInterministerielle_commune_arrondissement_label",
    -- source region
      NULL as source_region,
    -- update /creation date
      root.updated_at as updated_at,
      root.created_at as created_at
   FROM "ademe" root
   -- siret => beneficiaire
   LEFT JOIN ref_siret rs ON root.siret_beneficiaire = rs.code
   LEFT JOIN ref_categorie_juridique rs_rcj ON rs.categorie_juridique = rs_rcj.code
   LEFT JOIN ref_qpv rs_rqpv ON rs.code_qpv = rs_rqpv.code
   LEFT JOIN ref_commune rs_rc ON rs.code_commune = rs_rc.code
   LEFT JOIN ref_arrondissement rs_rc_ra ON rs_rc.code_arrondissement = rs_rc_ra.code 
;