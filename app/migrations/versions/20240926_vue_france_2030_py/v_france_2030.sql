CREATE VIEW public.v_france_2030 AS
SELECT fr.date_dpm, fr.operateur, fr.procedure, fr.nom_projet, fr.typologie, fr.nom_strategie, fr.montant_subvention, fr.montant_avance_remboursable, fr.montant_aide, fr.siret, fr.code_nomenclature, fr.annee,
infos_fr.numero, infos_fr.mot, infos_fr.phrase,
siret.categorie_juridique, siret.code_commune, siret.denomination as nom_beneficiaire, siret.adresse, siret.code_qpv,
commune.label_commune, commune.code_crte, commune.label_crte, commune.code_region, commune.label_region, commune.code_epci, commune.label_epci, commune.code_departement, commune.label_departement, commune.is_pvd, commune.date_pvd, commune.is_acv, commune.date_acv,
arr.code as code_arrondissement, arr.label as label_arrondissement, ref_typologie."Categorie_typologie" as categorie_typologie, codif_reg."Code_iso-3166-2" as code_iso_region
FROM france_2030 as fr LEFT JOIN nomenclature_france_2030 as infos_fr ON fr.code_nomenclature = infos_fr.code
LEFT JOIN ref_siret as siret ON fr.siret = siret.code
LEFT JOIN ref_commune as commune ON siret.code_commune = commune.code
LEFT JOIN ref_arrondissement as arr ON commune.code_arrondissement = arr.code
LEFT JOIN "SGAR"."FR30_typologie" as ref_typologie ON ref_typologie."Typologie" = fr.typologie
LEFT JOIN "SGAR"."codification_regions" as codif_reg ON commune.code_region = codif_reg."Code_region"