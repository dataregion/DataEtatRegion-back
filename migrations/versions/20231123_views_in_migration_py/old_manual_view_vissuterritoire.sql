---- 
---- Script manuel rappatrié pour être intégré dans les migrations
----
CREATE MATERIALIZED VIEW budget_summary AS
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
FROM flatten_summarized_ae
UNION
SELECT ademe.id AS id,
       date_part('year', ademe.date_convention) AS annee,
       ademe.montant AS montant_ae,
       ademe.montant AS montant_cp,
       'ADEME' AS programme,
       rs.code AS siret,
       rc.code AS code_commune,
       rc.code_departement,
       rc.code_crte,
       rc.code_epci,
       rs.code_qpv AS "code_qpv",
       rcj.type AS "categorie_juridique",
       NULL AS "loc_inter",
       NULL AS "code_departement_loc_inter",
       NULL AS "code_commune_loc_inter",
       NULL AS "code_epci_loc_inter",
       NULL AS "code_crte_loc_inter"
FROM "ademe" ademe
LEFT JOIN ref_siret rs ON ademe.siret_beneficiaire = rs.code
LEFT JOIN ref_commune rc ON rs.code_commune = rc.code
LEFT JOIN ref_categorie_juridique rcj ON rs.categorie_juridique = rcj.code
WHERE rc.code IS NOT NULL;


CREATE INDEX idx_groupby_commune ON budget_summary (annee, code_programme, categorie_juridique, code_commune, montant_ae, montant_cp);
CREATE INDEX idx_groupby_departement ON budget_summary (annee, code_programme, categorie_juridique, code_departement, montant_ae, montant_cp);
CREATE INDEX idx_groupby_crte ON budget_summary (annee, code_programme, categorie_juridique, code_crte, montant_ae, montant_cp);
CREATE INDEX idx_groupby_epci ON budget_summary (annee, code_programme, categorie_juridique, code_epci, montant_ae, montant_cp);


-----
CREATE MATERIALIZED VIEW m_summary_annee_geo_type_bop AS
SELECT DISTINCT annee,
                code_programme,
                code_commune,
                code_departement,
                code_crte,
                code_epci,
                code_qpv,
                siret,
                categorie_juridique
FROM public.budget_summary
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
FROM public.budget_summary
WHERE code_departement_loc_inter != '';


CREATE INDEX idx_groupby_summary_commune ON m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_commune);
CREATE INDEX idx_groupby_summary_departement ON m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_departement);
CREATE INDEX idx_groupby_summary_epci ON m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_epci);
CREATE INDEX idx_groupby_summary_crte ON m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_crte);


-----
CREATE MATERIALIZED VIEW m_montant_par_niveau_bop_annee_type AS
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_commune = s.code_commune
          OR fce.code_commune_loc_inter = s.code_commune)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM budget_summary fce
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
FROM m_summary_annee_geo_type_bop s
WHERE s.code_commune IS NOT NULL
GROUP BY s.annee,
         s.code_programme,
         s.categorie_juridique,
         s.code_commune
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_departement = s.code_departement
          OR fce.code_departement_loc_inter = s.code_departement)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM budget_summary fce
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
FROM m_summary_annee_geo_type_bop s
WHERE s.code_departement IS NOT NULL
GROUP BY s.annee,
         s.code_programme,
         s.categorie_juridique,
         s.code_departement
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_epci = s.code_epci
          OR fce.code_epci_loc_inter = s.code_epci)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM budget_summary fce
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
FROM m_summary_annee_geo_type_bop s
WHERE s.code_epci IS NOT NULL
GROUP BY s.annee,
         s.code_programme,
         s.categorie_juridique,
         s.code_epci
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND (fce.code_crte = s.code_crte
          OR fce.code_crte_loc_inter = s.code_crte)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM budget_summary fce
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
FROM m_summary_annee_geo_type_bop s
WHERE s.code_crte IS NOT NULL
GROUP BY s.annee,
         s.code_programme,
         s.categorie_juridique,
         s.code_crte
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.code_qpv = s.code_qpv
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM budget_summary fce
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
FROM m_summary_annee_geo_type_bop s
WHERE s.code_qpv IS NOT NULL
GROUP BY s.annee,
         s.code_programme,
         s.categorie_juridique,
         s.code_qpv;


CREATE OR REPLACE VIEW montant_par_niveau_bop_annee_type AS
SELECT *
FROM public.m_montant_par_niveau_bop_annee_type;