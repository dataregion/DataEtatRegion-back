CREATE MATERIALIZED VIEW flatten_financial_lines_data_qpv AS
    SELECT *
    FROM _flatten_financial_lines ffl
   WHERE ffl.lieu_action_code_qpv IS NOT NULL;


CREATE INDEX idx_fflqpv_annees ON public.flatten_financial_lines_data_qpv (annee);
CREATE INDEX idx_fflqpv_beneficiaire_code ON public.flatten_financial_lines_data_qpv (beneficiaire_code);
CREATE INDEX idx_fflqpv_programme_theme ON public.flatten_financial_lines_data_qpv (programme_theme);
CREATE INDEX idx_fflqpv_beneficiaire_categorieJuridique_type ON public.flatten_financial_lines_data_qpv ("beneficiaire_categorieJuridique_type");
CREATE INDEX idx_fflqpv_centreCouts_description ON public.flatten_financial_lines_data_qpv ("centreCouts_description");