CREATE MATERIALIZED VIEW vt_flatten_summarized_ae AS
	   SELECT
               'FINANCIAL_DATA_AE' as SOURCE,
               fce.id as id,
               fce.n_poste_ej,
               fce.n_ej,
               fce.source_region as source_region,
               fce.annee as annee,
               fce.contrat_etat_region,
               SUM(mce.montant) as montant_ae,
			   SUM(fcp.montant) as montant_cp,
			   max(fcp.date_derniere_operation_dp) as date_dernier_paiement,
			   rdf.code as code_domaine_fonctionnel,
			   rdf.label as label_domaine_fonctionnel,
			   rt."label" as theme,
               rcp.code as code_programme,
               rcp.label as label_programme,
               rp.code as ref_programmation,
               rp.label as label_ref_programmation,
               rs.code as siret,
               rs.denomination as denomination,
               rc.code as code_commune,
               rc.code_departement,
               rc.code_crte,
               rc.code_epci,
               rs.code_qpv AS "code_qpv",
               rcj.type AS "categorie_juridique",
               rli.code as "loc_inter",
               rli."label" as label_loc_inter,
               substring(rli.code,4,2) as "code_departement_loc_inter",
               rc2.code as "code_commune_loc_inter",
               rc2.code_epci as "code_epci_loc_inter",
               rc2.code_crte as "code_crte_loc_inter"
           FROM "financial_ae" fce
           LEFT JOIN montant_financial_ae mce ON fce.id = mce.id_financial_ae
		   LEFT join financial_cp fcp ON fcp.id_ae = fce.id
           LEFT JOIN ref_siret rs ON fce.siret = rs.code
           LEFT JOIN ref_commune rc ON rs.code_commune = rc.code
           LEFT JOIN ref_categorie_juridique rcj ON rs.categorie_juridique = rcj.code
           LEFT join ref_localisation_interministerielle rli on rli.code = fce.localisation_interministerielle
           LEFT join ref_commune rc2 on rc2.id = rli.commune_id
           left join ref_domaine_fonctionnel rdf on rdf.code = fce.domaine_fonctionnel
           left join ref_code_programme rcp on rcp.code = fce.programme
           left join ref_theme rt on rt.id = rcp.theme
           left join ref_programmation rp on rp.code = fce.referentiel_programmation
           WHERE rc.code IS NOT NULL
           GROUP BY fce.id,   fce.n_poste_ej, fce.source_region ,fce.contrat_etat_region,rt.label,
               fce.n_ej, rc.id,rs.code_qpv,rs.code,rdf.code,rdf.label, rp.code,rp."label", rcp.code, rcp.label ,rcj.type , rs.denomination ,
           rli.code, rc2.code, rc2.code_epci,  rli."label" ,rc2.code_crte, rc2.code_arrondissement;