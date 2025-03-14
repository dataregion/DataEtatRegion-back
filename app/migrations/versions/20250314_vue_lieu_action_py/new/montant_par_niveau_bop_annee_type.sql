CREATE OR REPLACE VIEW montant_par_niveau_bop_annee_type AS
 SELECT vt_m_montant_par_niveau_bop_annee_type.montant_ae,
    vt_m_montant_par_niveau_bop_annee_type.montant_cp,
    vt_m_montant_par_niveau_bop_annee_type.niveau,
    vt_m_montant_par_niveau_bop_annee_type.annee,
    vt_m_montant_par_niveau_bop_annee_type.source,
    vt_m_montant_par_niveau_bop_annee_type.programme,
    vt_m_montant_par_niveau_bop_annee_type.code,
    vt_m_montant_par_niveau_bop_annee_type.type
   FROM vt_m_montant_par_niveau_bop_annee_type;