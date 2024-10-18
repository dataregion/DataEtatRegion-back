CREATE MATERIALIZED VIEW flatten_financial_lines AS
    SELECT *
    FROM flatten_ae
    UNION ALL
    SELECT *
    FROM flatten_ademe;

