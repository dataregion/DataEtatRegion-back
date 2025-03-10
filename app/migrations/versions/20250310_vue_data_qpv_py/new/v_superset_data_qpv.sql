CREATE VIEW superset_data_qpv AS
  SELECT ffl.*
    FROM flatten_financial_lines ffl
    WHERE ffl.beneficiaire_qpv_code IS NOT NULL OR ffl.beneficiaire_qpv24_code IS NOT NULL
  UNION ALL
  SELECT ffl.*
    FROM flatten_financial_lines ffl
    INNER JOIN qpv_lieu_action qla ON qla.n_ej = ffl.n_ej;
   