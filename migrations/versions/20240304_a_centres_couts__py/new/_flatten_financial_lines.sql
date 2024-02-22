CREATE OR REPLACE VIEW _flatten_financial_lines AS
    SELECT *
    FROM flatten_ae
    UNION ALL
    SELECT *
    FROM flatten_ademe
    UNION ALL
    SELECT *
    FROM flatten_orphan_cp;

-- Les objets dépendants de cette vue

DROP VIEW superset_lignes_financieres;

DROP MATERIALIZED VIEW flatten_financial_lines;

CREATE MATERIALIZED VIEW flatten_financial_lines AS
    SELECT *
    FROM _flatten_financial_lines;

CREATE VIEW superset_lignes_financieres AS
  SELECT *
  FROM flatten_financial_lines;