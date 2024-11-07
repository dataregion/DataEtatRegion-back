CREATE INDEX idx_groupby_summary_commune ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_commune);
CREATE INDEX idx_groupby_summary_departement ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_departement);
CREATE INDEX idx_groupby_summary_epci ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_epci);
CREATE INDEX idx_groupby_summary_crte ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_crte);
CREATE INDEX idx_groupby_summary_qpv ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_qpv);
CREATE INDEX idx_groupby_summary_qpv24 ON vt_m_summary_annee_geo_type_bop (annee, code_programme, categorie_juridique, code_qpv24);

CREATE MATERIALIZED VIEW vt_m_montant_par_niveau_bop_annee_type AS
     SELECT ( SELECT sum(fce.montant_ae) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND (fce.code_commune::text = s.code_commune::text OR fce.code_commune_loc_inter::text = s.code_commune::text) AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_ae,
    ( SELECT sum(fce.montant_cp) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND (fce.code_commune::text = s.code_commune::text OR fce.code_commune_loc_inter::text = s.code_commune::text) AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_cp,
    'commune'::text AS niveau,
    s.annee,
    s.source,
    s.code_programme AS programme,
    s.code_commune AS code,
    s.categorie_juridique AS type
   FROM vt_m_summary_annee_geo_type_bop s
  WHERE s.code_commune IS NOT NULL
  GROUP BY s.annee, s.source, s.code_programme, s.categorie_juridique, s.code_commune
UNION
 SELECT ( SELECT sum(fce.montant_ae) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND (fce.code_departement::text = s.code_departement::text OR fce.code_departement_loc_inter = s.code_departement::text) AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_ae,
    ( SELECT sum(fce.montant_cp) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND (fce.code_departement::text = s.code_departement::text OR fce.code_departement_loc_inter = s.code_departement::text) AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_cp,
    'departement'::text AS niveau,
    s.annee,
    s.source,
    s.code_programme AS programme,
    s.code_departement AS code,
    s.categorie_juridique AS type
   FROM vt_m_summary_annee_geo_type_bop s
  WHERE s.code_departement IS NOT NULL
  GROUP BY s.annee, s.source, s.code_programme, s.categorie_juridique, s.code_departement
UNION
 SELECT ( SELECT sum(fce.montant_ae) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND (fce.code_epci::text = s.code_epci::text OR fce.code_epci_loc_inter::text = s.code_epci::text) AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_ae,
    ( SELECT sum(fce.montant_cp) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND (fce.code_epci::text = s.code_epci::text OR fce.code_epci_loc_inter::text = s.code_epci::text) AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_cp,
    'epci'::text AS niveau,
    s.annee,
    s.source,
    s.code_programme AS programme,
    s.code_epci AS code,
    s.categorie_juridique AS type
   FROM vt_m_summary_annee_geo_type_bop s
  WHERE s.code_epci IS NOT NULL
  GROUP BY s.annee, s.source, s.code_programme, s.categorie_juridique, s.code_epci
UNION
 SELECT ( SELECT sum(fce.montant_ae) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND (fce.code_crte::text = s.code_crte::text OR fce.code_crte_loc_inter::text = s.code_crte::text) AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_ae,
    ( SELECT sum(fce.montant_cp) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND (fce.code_crte::text = s.code_crte::text OR fce.code_crte_loc_inter::text = s.code_crte::text) AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_cp,
    'crte'::text AS niveau,
    s.annee,
    s.source,
    s.code_programme AS programme,
    s.code_crte AS code,
    s.categorie_juridique AS type
   FROM vt_m_summary_annee_geo_type_bop s
  WHERE s.code_crte IS NOT NULL
  GROUP BY s.annee, s.source, s.code_programme, s.categorie_juridique, s.code_crte
UNION
 SELECT ( SELECT sum(fce.montant_ae) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND fce.code_qpv::text = s.code_qpv::text AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_ae,
    ( SELECT sum(fce.montant_cp) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND fce.code_qpv::text = s.code_qpv::text AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_cp,
    'qpv'::text AS niveau,
    s.annee,
    s.source,
    s.code_programme AS programme,
    s.code_qpv AS code,
    s.categorie_juridique AS type
   FROM vt_m_summary_annee_geo_type_bop s
  WHERE s.code_qpv IS NOT NULL
  GROUP BY s.annee, s.source, s.code_programme, s.categorie_juridique, s.code_qpv
UNION
 SELECT ( SELECT sum(fce.montant_ae) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND fce.code_qpv::text = s.code_qpv24::text AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_ae,
    ( SELECT sum(fce.montant_cp) AS sum
           FROM vt_budget_summary fce
          WHERE fce.code_programme::text = s.code_programme::text AND fce.annee = s.annee AND fce.source = s.source AND fce.code_qpv::text = s.code_qpv24::text AND (fce.categorie_juridique::text = s.categorie_juridique::text OR fce.categorie_juridique IS NULL AND s.categorie_juridique IS NULL)) AS montant_cp,
    'qpv24'::text AS niveau,
    s.annee,
    s.source,
    s.code_programme AS programme,
    s.code_qpv24 AS code,
    s.categorie_juridique AS type
   FROM vt_m_summary_annee_geo_type_bop s
  WHERE s.code_qpv IS NOT NULL
  GROUP BY s.annee, s.source, s.code_programme, s.categorie_juridique, s.code_qpv24;