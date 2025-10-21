CREATE MATERIALIZED VIEW flatten_financial_lines_data_qpv AS
    SELECT *
    FROM _flatten_financial_lines ffl
   WHERE ffl.lieu_action_code_qpv IS NOT NULL;
