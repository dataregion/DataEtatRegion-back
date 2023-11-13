CREATE MATERIALIZED VIEW flatten_summarized_ademe AS
       SELECT 
              'ADEME' as SOURCE, -- Le data type
              ademe.id AS id,
              date_part('year', ademe.date_convention) AS annee,
              ademe.montant AS montant_ae,
              ademe.montant AS montant_cp,
              'ADEME' AS code_programme,
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