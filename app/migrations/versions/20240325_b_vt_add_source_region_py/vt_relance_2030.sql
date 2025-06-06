CREATE SCHEMA IF NOT EXISTS france_relance;

CREATE TABLE IF NOT EXISTS france_relance."LocalisationBretagne" (
	"Commune" varchar(56) NOT NULL,
	code_postal int4 NULL,
	"CodeInsee" int4 NULL,
	region varchar(8) NOT NULL,
	departement varchar(15) NULL,
	arrondissement varchar(14) NULL,
	canton varchar(25) NULL,
	epci varchar(59) NULL,
	siren_epci int4 NULL,
	numero_departement int4 NULL,
	numero_arrondissement int4 NULL,
	numero_canton int4 NULL,
	lattitude_2 numeric(11, 8) NULL,
	longitude_2 numeric(11, 8) NULL,
	géoloc_globale_en_virgules_2 varchar(31) NULL,
	numéro_siren int4 NOT NULL,
	genre_du_présidentmaire varchar(30) NULL,
	nom_du_maire_ou_pdt varchar(12) NULL,
	prénom_du_maire_pdt varchar(13) NULL,
	adresse_postale_du_siège_epci varchar(39) NULL,
	code_postal_siège_epci varchar(32) NULL,
	nature_juridique_epci varchar(26) NULL,
	adresse_mail_du_pdtmaire varchar(52) NULL,
	nom_pdt_epci varchar(25) NULL,
	mail_pdt_epci varchar(39) NULL,
	nom_dgs_epci varchar(27) NULL,
	mail_dgs_epci varchar(37) NULL,
	numéro_de_circonscription varchar(25) NULL,
	nom_du_député varchar(129) NULL,
	adresse_mail_de_contact_du_député varchar(222) NULL,
	crte varchar(44) NULL,
	code_region varchar DEFAULT '53' NULL,
	CONSTRAINT fichier_bretagne_pkey PRIMARY KEY ("Commune")
);

CREATE TABLE IF NOT EXISTS france_relance."Dispositifs" (
	dispositif varchar(174) NOT NULL,
	statut varchar(20) NULL,
	numéro_de_la_mesure int4 NULL,
	mesure_du_plan_de_relance varchar(147) NULL,
	type_de_mise_en_oeuvre varchar(42) NULL,
	porteurs varchar(62) NULL,
	cible varchar(112) NULL,
	enveloppe_nationale_du_dispositif varchar(15) NULL,
	dotation_régionale_du_dispositif varchar(15) NULL,
	début_du_dispositif date NULL,
	fin_du_dispositif date NULL,
	annonce_des_lauréats date NULL,
	lien_internet varchar(295) NULL,
	enveloppe_nationale_de_la_mesure varchar(15) NULL,
	enveloppe_régionale_de_la_mesure varchar(11) NULL,
	"SousaxeDuPlanDeRelance" varchar(69) NULL,
	"AxeDuPlanDeRelance" varchar(13) NULL,
	echelle varchar(13) NULL,
	ruo varchar(25) NULL,
	plan varchar(31) NULL,
	CONSTRAINT dispositifs_pkey PRIMARY KEY (dispositif)
);

CREATE TABLE IF NOT EXISTS france_relance."Laureats" (
	id serial NOT NULL,
	"Structure" varchar(91) NOT NULL,
	nombre_de_dossiers_lauréats int4 NOT NULL,
	"DétailsDuProjet" varchar(6836) NULL,
	"NuméroDeSiretSiConnu" int8 NULL,
	"SubventionAccordée" numeric(20, 2) NULL,
	"LauréatOuCandidat" varchar(8) NOT NULL,
	fichier_bretagne varchar(73) NULL,
	tous_les_dispositifs varchar(174) NOT NULL,
	lieu_précis_de_laction_financée_si_connu varchar(58) NULL,
	montant_subvention_demandée numeric(20, 2) NULL,
	montant_projet numeric(20, 2) NULL,
	"Synthèse" varchar(6835) NULL,
	montant_indicatif varchar(55) NOT NULL,
	date_de_renseignement_de_ce_formulaire date NOT NULL,
	information_communicable_cochez_si_oui varchar(7) NULL,
	collaborateurs varchar(19) NULL,
	genre_du_dirigeant varchar(8) NULL,
	prénom_du_dirigeante varchar(14) NULL,
	nom_du_dirigeante varchar(23) NULL,
	email_du_dirigeante varchar(38) NULL,
	téléphone_du_dirigeant varchar(31) NULL,
	adresse_postale varchar(87) NULL,
	autres_informations_importantes varchar(28) NULL,
	type_de_structure varchar(15) NULL,
	CONSTRAINT laureats_pkey PRIMARY KEY (id),
	CONSTRAINT laureats_fichier_bretagne_fkey FOREIGN KEY (fichier_bretagne) REFERENCES france_relance."LocalisationBretagne"("Commune"),
	CONSTRAINT laureats_tous_les_dispositifs_fkey FOREIGN KEY (tous_les_dispositifs) REFERENCES france_relance."Dispositifs"(dispositif)
);

CREATE OR REPLACE VIEW public.vt_relance_2030 AS
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
