CREATE OR REPLACE VIEW _flatten_financial_lines AS
    SELECT *
    FROM flatten_ae
    UNION ALL
    SELECT *
    FROM flatten_ademe
    UNION ALL
    SELECT *
    FROM flatten_orphan_cp;
