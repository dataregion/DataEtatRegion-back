--- Script manuel permettant de de corriger les associations commune en tenant compte des code parent

-- Requête a executer 3 fois

UPDATE ref_localisation_interministerielle r
SET commune_id = (SELECT commune_id FROM ref_localisation_interministerielle parent WHERE parent.code = r.code_parent)
where commune_id IS null