
CREATE INDEX idx_groupby_summary_commune ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_commune);
CREATE INDEX idx_groupby_summary_departement ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_departement);
CREATE INDEX idx_groupby_summary_epci ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_epci);
CREATE INDEX idx_groupby_summary_crte ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_crte);


CREATE MATERIALIZED VIEW vt_m_montant_par_niveau_bop_annee_type AS
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.source = s.source
     AND (fce.code_commune = s.code_commune
          OR fce.code_commune_loc_inter = s.code_commune)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.source = s.source
     AND (fce.code_commune = s.code_commune
          OR fce.code_commune_loc_inter = s.code_commune)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_cp,
       'commune' AS niveau,
       s.annee,
       s.source,
       s.code_programme as programme,
       s.code_commune AS code,
       s.categorie_juridique AS TYPE
FROM vt_m_summary_annee_geo_type_bop s
WHERE s.code_commune IS NOT NULL
GROUP BY s.annee,
         s.source,
         s.code_programme,
         s.categorie_juridique,
         s.code_commune
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.source = s.source
     AND (fce.code_departement = s.code_departement
          OR fce.code_departement_loc_inter = s.code_departement)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.source = s.source
     AND (fce.code_departement = s.code_departement
          OR fce.code_departement_loc_inter = s.code_departement)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_cp,
       'departement' AS niveau,
       s.annee,
       s.source,
       s.code_programme as programme,
       s.code_departement AS code,
       s.categorie_juridique AS TYPE
FROM vt_m_summary_annee_geo_type_bop s
WHERE s.code_departement IS NOT NULL
GROUP BY s.annee,
         s.source,
         s.code_programme,
         s.categorie_juridique,
         s.code_departement
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.source = s.source
     AND (fce.code_epci = s.code_epci
          OR fce.code_epci_loc_inter = s.code_epci)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.source = s.source
     AND (fce.code_epci = s.code_epci
          OR fce.code_epci_loc_inter = s.code_epci)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_cp,
       'epci' AS niveau,
       s.annee,
       s.source,
       s.code_programme as programme,
       s.code_epci AS code,
       s.categorie_juridique AS TYPE
FROM vt_m_summary_annee_geo_type_bop s
WHERE s.code_epci IS NOT NULL
GROUP BY s.annee,
         s.source,
         s.code_programme,
         s.categorie_juridique,
         s.code_epci
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.source = s.source
     AND (fce.code_crte = s.code_crte
          OR fce.code_crte_loc_inter = s.code_crte)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.source = s.source
     AND (fce.code_crte = s.code_crte
          OR fce.code_crte_loc_inter = s.code_crte)
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_cp,
       'crte' AS niveau,
       s.annee,
       s.source,
       s.code_programme as programme,
       s.code_crte AS code,
       s.categorie_juridique AS TYPE
FROM vt_m_summary_annee_geo_type_bop s
WHERE s.code_crte IS NOT NULL
GROUP BY s.annee,
         s.source,
         s.code_programme,
         s.categorie_juridique,
         s.code_crte
UNION
SELECT
  (SELECT SUM(fce.montant_ae)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.source = s.source
     AND fce.code_qpv = s.code_qpv
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_ae,

  (SELECT SUM(fce.montant_cp)
   FROM vt_budget_summary fce
   WHERE fce.code_programme = s.code_programme
     AND fce.annee = s.annee
     AND fce.source = s.source
     AND fce.code_qpv = s.code_qpv
     AND (fce.categorie_juridique = s.categorie_juridique
          OR (fce.categorie_juridique IS NULL
              AND s.categorie_juridique IS NULL))) AS montant_cp,
       'qpv' AS niveau,
       s.annee,
       s.source,
       s.code_programme as programme,
       s.code_qpv AS code,
       s.categorie_juridique AS TYPE
FROM vt_m_summary_annee_geo_type_bop s
WHERE s.code_qpv IS NOT NULL
GROUP BY s.annee,
         s.source,
         s.code_programme,
         s.categorie_juridique,
         s.code_qpv;