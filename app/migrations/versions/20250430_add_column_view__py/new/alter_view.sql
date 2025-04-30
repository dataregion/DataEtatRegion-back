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




