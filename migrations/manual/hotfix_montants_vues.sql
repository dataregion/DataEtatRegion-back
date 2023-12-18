------------------------------------------------------
--- Hotfix pour régler le soucis des montants engagés
--- C'est un hotfix pre refactoring des vues materialisés 
--- pour migration plus simple.
--- Il consiste uniquement en l'execution de ce script.
------------------------------------------------------
---------------------------------------------------- Renommage en old
alter materialized view flatten_ae 
rename to flatten_ae_old_13_12_2023;

alter materialized view flatten_financial_lines 
rename to flatten_financial_lines_old_13_12_2023;

alter materialized view vt_flatten_summarized_ae 
rename to vt_flatten_summarized_ae_lines_old_13_12_2023;

alter view superset_lignes_financieres
rename to superset_lignes_financieres_old_13_12_2023;

alter materialized view vt_budget_summary
rename to vt_budget_summary_old_13_12_2023;

alter materialized view vt_m_summary_annee_geo_type_bop
rename to vt_m_summary_annee_geo_type_bop_old_13_12_2023;

alter materialized view vt_m_montant_par_niveau_bop_annee_type
rename to vt_m_montant_par_niveau_bop_annee_type_old_13_12_2023;

alter view montant_par_niveau_bop_annee_type
rename to montant_par_niveau_bop_annee_type_old_13_12_2023;

----------------------------------------------------- Recréation des vues
------------------------- flatten_ae
CREATE MATERIALIZED VIEW flatten_ae AS
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
   left join (
       select
         root.id as id,
         SUM(mce.montant) as montant_ae
       FROM "financial_ae" root
       LEFT JOIN montant_financial_ae mce ON root.id = mce.id_financial_ae
       GROUP BY root.id
   ) aggr_mt_ae on aggr_mt_ae.id = root.id
   left join (
       select
         root.id as id,
         SUM(fcp.montant) as montant_cp,
         max(fcp.date_derniere_operation_dp) as date_dernier_paiement
       FROM "financial_ae" root
       LEFT JOIN financial_cp fcp ON fcp.id_ae = root.id
       GROUP BY root.id
   ) aggr_mt_cp on aggr_mt_cp.id = root.id
;

------------------------- flatten_financial_lines
CREATE MATERIALIZED VIEW flatten_financial_lines AS
    SELECT *
    FROM flatten_ae
    UNION ALL
    SELECT *
    FROM flatten_ademe;

------------------------- vt_flatten_summarized_ae
CREATE MATERIALIZED VIEW vt_flatten_summarized_ae AS
SELECT
   'FINANCIAL_DATA_AE' as SOURCE,
   fa.id as id,
   fa.n_poste_ej as "n_poste_ej",
   fa.n_ej as "n_ej",
   fa.source_region as "source_region",
   fa.annee as "annee",
   fa.contrat_etat_region as "contrat_etat_region",
   fa.montant_ae as "montant_ae",
   fa.montant_cp  as "montant_cp",
   fa."dateDeDernierPaiement"  as "date_dernier_paiement",
   fa."domaineFonctionnel_code" as "code_domaine_fonctionnel",
   fa."domaineFonctionnel_label" as "label_domaine_fonctionnel",
   fa.programme_theme as "theme",
   fa.programme_code as "code_programme",
   fa.programme_label  as "label_programme",
   fa."referentielProgrammation_code" as "ref_programmation",
   fa."referentielProgrammation_label" as "label_ref_programmation",
   fa.beneficiaire_code as "siret",
   fa.beneficiaire_denomination as "denomination",
   fa.beneficiaire_commune_code as "code_commune",
   fa."beneficiaire_commune_codeDepartement" as "code_departement",
   fa."beneficiaire_commune_codeCrte" as "code_crte",
   fa."beneficiaire_commune_codeEpci" as "code_epci",
   fa.beneficiaire_qpv_code  AS "code_qpv",
   fa."beneficiaire_categorieJuridique_type" AS "categorie_juridique",
   fa."localisationInterministerielle_code" as "loc_inter",
   fa."localisationInterministerielle_label" as "label_loc_inter",
   fa."localisationInterministerielle_codeDepartement" as "code_departement_loc_inter",
   fa."localisationInterministerielle_commune_code" as "code_commune_loc_inter",
   fa."localisationInterministerielle_commune_codeEpci" as "code_epci_loc_inter",
   fa."localisationInterministerielle_commune_codeCrte" as "code_crte_loc_inter"
FROM flatten_ae fa  
WHERE fa.beneficiaire_commune_code IS NOT null
order by source, id, n_ej, n_poste_ej, source_region, annee;

----------------------- superset_lignes_financieres
CREATE VIEW superset_lignes_financieres AS
  SELECT *
  FROM flatten_financial_lines;

----------------------- vues visuterritoire
---
--- Vues dediées à visuterritoire
---
CREATE MATERIALIZED VIEW vt_budget_summary AS
SELECT id,
       annee,
       montant_ae,
       montant_cp,
       code_programme,
       siret,
       code_commune,
       code_departement,
       code_crte,
       code_epci,
       code_qpv,
       categorie_juridique,
       loc_inter,
       code_departement_loc_inter,
       code_commune_loc_inter,
       code_epci_loc_inter,
       code_crte_loc_inter
FROM vt_flatten_summarized_ae
UNION
SELECT id,
       annee,
       montant_ae,
       montant_cp,
       code_programme,
       siret,
       code_commune,
       code_departement,
       code_crte,
       code_epci,
       code_qpv,
       categorie_juridique,
       loc_inter,
       code_departement_loc_inter,
       code_commune_loc_inter,
       code_epci_loc_inter,
       code_crte_loc_inter
FROM vt_flatten_summarized_ademe;

-----
CREATE MATERIALIZED VIEW vt_m_summary_annee_geo_type_bop AS
SELECT DISTINCT annee,
                code_programme,
                code_commune,
                code_departement,
                code_crte,
                code_epci,
                code_qpv,
                siret,
                categorie_juridique
FROM public.vt_budget_summary
UNION
SELECT DISTINCT annee,
                code_programme,
                code_commune_loc_inter,
                code_departement_loc_inter,
                code_crte_loc_inter,
                code_epci_loc_inter,
                NULL,
                NULL,
                categorie_juridique
FROM public.vt_budget_summary
WHERE code_departement_loc_inter != '';

-----
CREATE MATERIALIZED VIEW vt_m_montant_par_niveau_bop_annee_type AS
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_commune = s.code_commune
          OR fce.code_commune_loc_inter = s.code_commune)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_commune = s.code_commune
          OR fce.code_commune_loc_inter = s.code_commune)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_cp,
       'commune' AS niveau,
       s.annee,
       s.code_programme as programme,
       s.code_commune AS code,
       s.categorie_juridique AS TYPE
FROM vt_m_summary_annee_geo_type_bop s
WHERE s.code_commune IS NOT NULL
GROUP BY s.annee,
         s.code_programme,
         s.categorie_juridique,
         s.code_commune
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_departement = s.code_departement
          OR fce.code_departement_loc_inter = s.code_departement)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_departement = s.code_departement
          OR fce.code_departement_loc_inter = s.code_departement)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_cp,
       'departement' AS niveau,
       s.annee,
       s.code_programme as programme,
       s.code_departement AS code,
       s.categorie_juridique AS TYPE
FROM vt_m_summary_annee_geo_type_bop s
WHERE s.code_departement IS NOT NULL
GROUP BY s.annee,
         s.code_programme,
         s.categorie_juridique,
         s.code_departement
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_epci = s.code_epci
          OR fce.code_epci_loc_inter = s.code_epci)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_epci = s.code_epci
          OR fce.code_epci_loc_inter = s.code_epci)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_cp,
       'epci' AS niveau,
       s.annee,
       s.code_programme as programme,
       s.code_epci AS code,
       s.categorie_juridique AS TYPE
FROM vt_m_summary_annee_geo_type_bop s
WHERE s.code_epci IS NOT NULL
GROUP BY s.annee,
         s.code_programme,
         s.categorie_juridique,
         s.code_epci
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_crte = s.code_crte
          OR fce.code_crte_loc_inter = s.code_crte)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_crte = s.code_crte
          OR fce.code_crte_loc_inter = s.code_crte)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_cp,
       'crte' AS niveau,
       s.annee,
       s.code_programme as programme,
       s.code_crte AS code,
       s.categorie_juridique AS TYPE
FROM vt_m_summary_annee_geo_type_bop s
WHERE s.code_crte IS NOT NULL
GROUP BY s.annee,
         s.code_programme,
         s.categorie_juridique,
         s.code_crte
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.code_qpv = s.code_qpv
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.code_qpv = s.code_qpv
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_cp,
       'qpv' AS niveau,
       s.annee,
       s.code_programme as programme,
       s.code_qpv AS code,
       s.categorie_juridique AS TYPE
FROM vt_m_summary_annee_geo_type_bop s
WHERE s.code_qpv IS NOT NULL
GROUP BY s.annee,
         s.code_programme,
         s.categorie_juridique,
         s.code_qpv;


CREATE OR REPLACE VIEW montant_par_niveau_bop_annee_type AS
SELECT *
FROM public.vt_m_montant_par_niveau_bop_annee_type;

---------- Drop cascade old views
DROP MATERIALIZED VIEW flatten_ae_old_13_12_2023 CASCADE;

---------- Indexes
CREATE INDEX idx_groupby_commune ON vt_budget_summary (annee, code_programme, categorie_juridique, code_commune, montant_ae, montant_cp);
CREATE INDEX idx_groupby_departement ON vt_budget_summary (annee, code_programme, categorie_juridique, code_departement, montant_ae, montant_cp);
CREATE INDEX idx_groupby_crte ON vt_budget_summary (annee, code_programme, categorie_juridique, code_crte, montant_ae, montant_cp);
CREATE INDEX idx_groupby_epci ON vt_budget_summary (annee, code_programme, categorie_juridique, code_epci, montant_ae, montant_cp);


CREATE INDEX idx_groupby_summary_commune ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_commune);
CREATE INDEX idx_groupby_summary_departement ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_departement);
CREATE INDEX idx_groupby_summary_epci ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_epci);
CREATE INDEX idx_groupby_summary_crte ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_crte);