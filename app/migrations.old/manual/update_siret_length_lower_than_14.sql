
-- FIX en prod faire le 06/09/2023

-- Update les financial_ae ou la longueur du siret était < 14

UPDATE financial_ae SET siret = concat('0',siret) WHERE siret IN (

SELECT DISTINCT(siret) FROM financial_ae  WHERE LENGTH(siret) < 14 AND concat('0',siret) IN

(SELECT DISTINCT(concat('0',siret)) FROM financial_ae WHERE LENGTH(siret) < 14
INTERSECT
SELECT DISTINCT(code) FROM ref_siret WHERE code IN(SELECT distinct(concat('0',siret)) FROM financial_ae  WHERE LENGTH(siret) < 14))
)
