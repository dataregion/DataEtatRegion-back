CREATE VIEW public.vt_relance_2030 AS
SELECT 'REL'::text AS source,
       date_part('year', date_de_renseignement_de_ce_formulaire) AS annee,
       "Structure" AS nom_laureat,
       "NuméroDeSiretSiConnu"::text AS numero_siret,
       "SubventionAccordée" AS montant_accorde
FROM france_relance."Laureats"
WHERE "LauréatOuCandidat" = 'Lauréat'
UNION
SELECT 'FR30'::text AS source,
       annee as annee,
       nom_beneficiaire AS nom_laureat,
       siret AS numero_siret,
       montant_aide AS montant_accorde
FROM public.france_2030;
