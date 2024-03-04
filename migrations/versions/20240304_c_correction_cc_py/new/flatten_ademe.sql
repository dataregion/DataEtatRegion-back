-- public.flatten_ademe source
CREATE OR REPLACE VIEW public.flatten_ademe
AS SELECT 'ADEME'::text AS source,
    root.id,
    NULL::integer AS n_poste_ej,
    NULL::text AS n_ej,
    date_part('year'::text, root.date_convention) AS annee,
    NULL::text AS contrat_etat_region,
    NULL::text AS compte_budgetaire,
    root.montant AS montant_ae,
    root.montant AS montant_cp,
    NULL::timestamp without time zone AS "dateDeDernierPaiement",
    NULL::timestamp without time zone AS "dateDeCreation",
    NULL::text AS "domaineFonctionnel_code",
    root.objet::text AS "domaineFonctionnel_label",
    NULL::text AS "referentielProgrammation_code",
    root.objet::text AS "referentielProgrammation_label",
    NULL::text AS "groupeMarchandise_code",
    NULL::text AS "groupeMarchandise_label",
    'ADEME'::text AS programme_code,
    NULL::text AS programme_label,
    NULL::text AS programme_theme,
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
    NULL::text AS "localisationInterministerielle_code",
    NULL::text AS "localisationInterministerielle_label",
    NULL::text AS "localisationInterministerielle_codeDepartement",
    NULL::text AS "localisationInterministerielle_commune_code",
    NULL::text AS "localisationInterministerielle_commune_label",
    NULL::text AS "localisationInterministerielle_commune_codeRegion",
    NULL::text AS "localisationInterministerielle_commune_labelRegion",
    NULL::text AS "localisationInterministerielle_commune_codeDepartement",
    NULL::text AS "localisationInterministerielle_commune_labelDepartement",
    NULL::text AS "localisationInterministerielle_commune_codeEpci",
    NULL::text AS "localisationInterministerielle_commune_labelEpci",
    NULL::text AS "localisationInterministerielle_commune_codeCrte",
    NULL::text AS "localisationInterministerielle_commune_labelCrte",
    NULL::text AS "localisationInterministerielle_commune_arrondissement_code",
    NULL::text AS "localisationInterministerielle_commune_arrondissement_label",
    NULL::text AS source_region,
    root.updated_at,
    root.created_at,
    NULL::text as "centreCouts_code",
    NULL::text as "centreCouts_label",
    NULL::text as "centreCouts_description"
   FROM ademe root
     LEFT JOIN ref_siret rs ON root.siret_beneficiaire::text = rs.code::text
     LEFT JOIN ref_categorie_juridique rs_rcj ON rs.categorie_juridique::text = rs_rcj.code::text
     LEFT JOIN ref_qpv rs_rqpv ON rs.code_qpv::text = rs_rqpv.code::text
     LEFT JOIN ref_commune rs_rc ON rs.code_commune::text = rs_rc.code::text
     LEFT JOIN ref_arrondissement rs_rc_ra ON rs_rc.code_arrondissement::text = rs_rc_ra.code::text;