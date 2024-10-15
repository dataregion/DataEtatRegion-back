CREATE OR REPLACE VIEW public.flatten_orphan_cp
    AS  SELECT 'FINANCIAL_DATA_CP'::text AS source,
    root.id,
    NULL::integer AS n_poste_ej,
    NULL::character varying AS n_ej,
    root.annee,
    root.contrat_etat_region,
    root.compte_budgetaire,
    root.montant AS montant_ae,
    root.montant AS montant_cp,
    root.date_derniere_operation_dp AS "dateDeDernierPaiement",
    NULL::date AS "dateDeCreation",
    rdf.code AS "domaineFonctionnel_code",
    rdf.label AS "domaineFonctionnel_label",
    rp.code AS "referentielProgrammation_code",
    rp.label AS "referentielProgrammation_label",
    rgm.code AS "groupeMarchandise_code",
    rgm.label AS "groupeMarchandise_label",
    rcp.code AS programme_code,
    rcp.label AS programme_label,
    rcp_rt.label AS programme_theme,
    rs.code AS beneficiaire_code,
    rs.denomination AS beneficiaire_denomination,
    rs_rcj.type AS "beneficiaire_categorieJuridique_type",
    rs_rqpv.code AS beneficiaire_qpv_code,
    rs_rqpv.label AS beneficiaire_qpv_label,
    rs_rc.code AS beneficiaire_commune_code,
    rs_rc.label_commune AS beneficiaire_commune_label,
    rs_rc.code_region AS "beneficiaire_commune_codeRegion",
    rs_rc.label_region AS "beneficiaire_commune_labelRegion",
    rs_rc.code_departement AS "beneficiaire_commune_codeDepartement",
    rs_rc.label_departement AS "beneficiaire_commune_labelDepartement",
    rs_rc.code_epci AS "beneficiaire_commune_codeEpci",
    rs_rc.label_epci AS "beneficiaire_commune_labelEpci",
    rs_rc.code_crte AS "beneficiaire_commune_codeCrte",
    rs_rc.label_crte AS "beneficiaire_commune_labelCrte",
    rs_rc_ra.code AS beneficiaire_commune_arrondissement_code,
    rs_rc_ra.label AS beneficiaire_commune_arrondissement_label,
    rli.code AS "localisationInterministerielle_code",
    rli.label AS "localisationInterministerielle_label",
    "substring"(rli.code::text, 4, 2) AS "localisationInterministerielle_codeDepartement",
    rli_rc.code AS "localisationInterministerielle_commune_code",
    rli_rc.label_commune AS "localisationInterministerielle_commune_label",
    rli_rc.code_region AS "localisationInterministerielle_commune_codeRegion",
    rli_rc.label_region AS "localisationInterministerielle_commune_labelRegion",
    rli_rc.code_departement AS "localisationInterministerielle_commune_codeDepartement",
    rli_rc.label_departement AS "localisationInterministerielle_commune_labelDepartement",
    rli_rc.code_epci AS "localisationInterministerielle_commune_codeEpci",
    rli_rc.label_epci AS "localisationInterministerielle_commune_labelEpci",
    rli_rc.code_crte AS "localisationInterministerielle_commune_codeCrte",
    rli_rc.label_crte AS "localisationInterministerielle_commune_labelCrte",
    rli_rc_ra.code AS "localisationInterministerielle_commune_arrondissement_code",
    rli_rc_ra.label AS "localisationInterministerielle_commune_arrondissement_label",
    root.source_region,
    root.updated_at,
    root.created_at,
    rcc.code AS "centreCouts_code",
    rcc.label AS "centreCouts_label",
    rcc.description AS "centreCouts_description"
   FROM financial_cp root
     LEFT JOIN ref_siret rs ON root.siret::text = rs.code::text
     LEFT JOIN ref_categorie_juridique rs_rcj ON rs.categorie_juridique::text = rs_rcj.code::text
     LEFT JOIN ref_qpv rs_rqpv ON rs.code_qpv::text = rs_rqpv.code::text
     LEFT JOIN ref_commune rs_rc ON rs.code_commune::text = rs_rc.code::text
     LEFT JOIN ref_arrondissement rs_rc_ra ON rs_rc.code_arrondissement::text = rs_rc_ra.code::text
     LEFT JOIN ref_localisation_interministerielle rli ON rli.code::text = root.localisation_interministerielle::text
     LEFT JOIN ref_commune rli_rc ON rli_rc.id = rli.commune_id
     LEFT JOIN ref_arrondissement rli_rc_ra ON rli_rc.code_arrondissement::text = rli_rc_ra.code::text
     LEFT JOIN ref_domaine_fonctionnel rdf ON rdf.code::text = root.domaine_fonctionnel::text
     LEFT JOIN ref_code_programme rcp ON rcp.code::text = root.programme::text
     LEFT JOIN ref_theme rcp_rt ON rcp_rt.id = rcp.theme
     LEFT JOIN ref_programmation rp ON rp.code::text = root.referentiel_programmation::text
     LEFT JOIN ref_groupe_marchandise rgm ON root.groupe_marchandise::text = rgm.code::text
     LEFT JOIN ref_centre_couts rcc ON root.centre_couts::text = rcc.code::text
  WHERE root.id_ae IS NULL;