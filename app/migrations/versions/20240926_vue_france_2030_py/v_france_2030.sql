CREATE TABLE IF NOT EXISTS "SGAR"."FR30_typologie" (
	"Categorie_typologie" text NULL,
  "Typologie" text NULL
);

TRUNCATE TABLE "SGAR"."FR30_typologie";
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Organismes publics', 'EP');
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Organismes publics', 'Fondation');
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Organismes publics', 'Organismes de recherche');
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Organismes publics', NULL);
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Entreprises', 'ETI');
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Entreprises', 'GE');
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Entreprises', 'PME');
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Entreprises', 'Personne physique');
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Entreprises', 'TPE');
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Entreprises', 'Associations');
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Autres', 'Collectivités');
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Autres', 'Autres');
INSERT INTO "SGAR"."FR30_typologie" VALUES ('Autres', 'Collectivités territoriales et/ou leur groupement');

CREATE TABLE IF NOT EXISTS "SGAR".codification_regions (
	"Region" text NULL,
	"Code_iso-3166-2" text NULL,
	"Code_region" text NULL
);

TRUNCATE TABLE "SGAR".codification_regions;
INSERT INTO "SGAR".codification_regions VALUES ('Auvergne-Rhône-Alpes', 'FR-ARA', '84');
INSERT INTO "SGAR".codification_regions VALUES ('Bourgogne-Franche-Comté', 'FR-BFC', '27');
INSERT INTO "SGAR".codification_regions VALUES ('Bretagne', 'FR-BRE', '53');
INSERT INTO "SGAR".codification_regions VALUES ('Centre-Val de Loire', 'FR-CVL', '24');
INSERT INTO "SGAR".codification_regions VALUES ('Corse', 'FR-20R', '94');
INSERT INTO "SGAR".codification_regions VALUES ('Grand Est', 'FR-GES', '44');
INSERT INTO "SGAR".codification_regions VALUES ('Guadeloupe', 'FR-971', '01');
INSERT INTO "SGAR".codification_regions VALUES ('Guyane', 'FR-973', '03');
INSERT INTO "SGAR".codification_regions VALUES ('Hauts-de-France', 'FR-HDF', '32');
INSERT INTO "SGAR".codification_regions VALUES ('Île-de-France', 'FR-IDF', '11');
INSERT INTO "SGAR".codification_regions VALUES ('La Réunion', 'FR-974', '04');
INSERT INTO "SGAR".codification_regions VALUES ('Martinique', 'FR-972', '02');
INSERT INTO "SGAR".codification_regions VALUES ('Mayotte', 'FR-976', '06');
INSERT INTO "SGAR".codification_regions VALUES ('Normandie', 'FR-NOR', '28');
INSERT INTO "SGAR".codification_regions VALUES ('Nouvelle-Aquitaine', 'FR-NAQ', '75');
INSERT INTO "SGAR".codification_regions VALUES ('Occitanie', 'FR-OCC', '76');
INSERT INTO "SGAR".codification_regions VALUES ('Pays de la Loire', 'FR-PDL', '52');
INSERT INTO "SGAR".codification_regions VALUES ('Provence-Alpes-Côte d''Azur', 'FR-PAC', '93');

CREATE OR REPLACE VIEW public.v_france_2030 AS
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