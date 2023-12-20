CREATE MATERIALIZED VIEW vt_flatten_summarized_ademe AS
SELECT 
       'ADEME' as SOURCE, -- Le data type
       fa.id AS "id",
       fa.annee  AS "annee",
       fa.montant_ae AS "montant_ae",
       fa.montant_cp AS "montant_cp",
       'ADEME' AS "code_programme",
       fa.beneficiaire_code AS "siret",
       fa.beneficiaire_commune_code AS "code_commune",
       fa."beneficiaire_commune_codeDepartement" as "code_departement",
       fa."beneficiaire_commune_codeCrte" as "code_crte",
       fa."beneficiaire_commune_codeEpci" as "code_epci",
       fa.beneficiaire_qpv_code AS "code_qpv",
       fa."beneficiaire_categorieJuridique_type" AS "categorie_juridique",
       NULL AS "loc_inter",
       NULL AS "code_departement_loc_inter",
       NULL AS "code_commune_loc_inter",
       NULL AS "code_epci_loc_inter",
       NULL AS "code_crte_loc_inter"
from flatten_ademe fa
WHERE fa.beneficiaire_commune_code IS NOT null
order by SOURCE, id;