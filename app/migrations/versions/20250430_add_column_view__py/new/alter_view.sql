CREATE MATERIALIZED VIEW flatten_financial_lines_new AS
    SELECT *
    FROM _flatten_financial_lines;


DROP VIEW superset_lignes_financieres;
DROP MATERIALIZED VIEW flatten_financial_lines;


alter materialized view flatten_financial_lines_new 
rename to flatten_financial_lines;

CREATE OR REPLACE VIEW superset_lignes_financieres AS
  SELECT *
  FROM flatten_financial_lines;


CREATE INDEX IF NOT EXISTS idx_ffl_source_programme_annee ON public.flatten_financial_lines (source_region, annee,programme_code);
CREATE INDEX IF NOT EXISTS idx_ffl_source_annee ON public.flatten_financial_lines (source_region, annee);
CREATE INDEX IF NOT EXISTS idx_ffl_source_programme ON flatten_financial_lines (source_region, programme_code);
CREATE INDEX IF NOT EXISTS idx_ffl_codes_qpv ON public.flatten_financial_lines USING btree (beneficiaire_qpv24_code, beneficiaire_qpv_code);