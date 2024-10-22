CREATE MATERIALIZED VIEW vt_m_summary_annee_geo_type_bop AS
    SELECT DISTINCT vt_budget_summary.annee,
        vt_budget_summary.source,
        vt_budget_summary.code_programme,
        vt_budget_summary.code_commune,
        vt_budget_summary.code_departement,
        vt_budget_summary.code_crte,
        vt_budget_summary.code_epci,
        vt_budget_summary.code_qpv,
        vt_budget_summary.code_qpv24,
        vt_budget_summary.siret,
        vt_budget_summary.categorie_juridique
    FROM vt_budget_summary
    UNION
    SELECT DISTINCT vt_budget_summary.annee,
        vt_budget_summary.source,
        vt_budget_summary.code_programme,
        vt_budget_summary.code_commune_loc_inter AS code_commune,
        vt_budget_summary.code_departement_loc_inter AS code_departement,
        vt_budget_summary.code_crte_loc_inter AS code_crte,
        vt_budget_summary.code_epci_loc_inter AS code_epci,
        NULL::text AS code_qpv,
        NULL::text AS code_qpv24,
        NULL::text AS siret,
        vt_budget_summary.categorie_juridique
    FROM vt_budget_summary
    WHERE vt_budget_summary.code_departement_loc_inter <> ''::text;