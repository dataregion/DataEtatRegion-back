CREATE MATERIALIZED VIEW flatten_financial_lines_new AS
    SELECT *
    FROM _flatten_financial_lines;


DROP VIEW superset_lignes_financieres CASCADE;
DROP MATERIALIZED VIEW flatten_financial_lines CASCADE;


alter materialized view flatten_financial_lines_new 
rename to flatten_financial_lines;

CREATE OR REPLACE VIEW superset_lignes_financieres AS
  SELECT *
  FROM flatten_financial_lines;


CREATE VIEW _superset_lignes_financieres_52 AS SELECT * FROM superset_lignes_financieres WHERE source_region = '52';

CREATE MATERIALIZED VIEW IF NOT EXISTS superset_lignes_financieres_52 AS SELECT * FROM _superset_lignes_financieres_52;


CREATE INDEX idx_ffl_codes_qpv ON public.flatten_financial_lines USING btree (beneficiaire_qpv24_code, beneficiaire_qpv_code);
CREATE INDEX idx_ffl_id ON public.flatten_financial_lines USING btree (id);
CREATE INDEX idx_ffl_source_annee ON public.flatten_financial_lines USING btree (source_region, annee);
CREATE INDEX idx_ffl_source_programme ON public.flatten_financial_lines USING btree (source_region, programme_code);
CREATE INDEX idx_ffl_source_programme_annee ON public.flatten_financial_lines USING btree (source_region, annee, programme_code);
CREATE INDEX index_ffl_beneficiaire_categoriejuridique_type ON public.flatten_financial_lines USING btree ("beneficiaire_categorieJuridique_type");
CREATE INDEX index_ffl_beneficiaire_commune_arrondissement_code ON public.flatten_financial_lines USING btree (beneficiaire_commune_arrondissement_code);
CREATE INDEX index_ffl_beneficiaire_commune_code ON public.flatten_financial_lines USING btree (beneficiaire_commune_code);
CREATE INDEX index_ffl_beneficiaire_commune_codecrte ON public.flatten_financial_lines USING btree ("beneficiaire_commune_codeCrte");
CREATE INDEX index_ffl_beneficiaire_commune_codedepartement ON public.flatten_financial_lines USING btree ("beneficiaire_commune_codeDepartement");
CREATE INDEX index_ffl_beneficiaire_commune_codeepci ON public.flatten_financial_lines USING btree ("beneficiaire_commune_codeEpci");
CREATE INDEX index_ffl_beneficiaire_commune_coderegion ON public.flatten_financial_lines USING btree ("beneficiaire_commune_codeRegion");
CREATE INDEX index_ffl_localisationinterministerielle_code ON public.flatten_financial_lines USING btree ("localisationInterministerielle_code");
CREATE INDEX index_ffl_localisationinterministerielle_commune_arrondissement ON public.flatten_financial_lines USING btree ("localisationInterministerielle_commune_arrondissement_code");
CREATE INDEX index_ffl_localisationinterministerielle_commune_code ON public.flatten_financial_lines USING btree ("localisationInterministerielle_commune_code");
CREATE INDEX index_ffl_localisationinterministerielle_commune_codecrte ON public.flatten_financial_lines USING btree ("localisationInterministerielle_commune_codeCrte");
CREATE INDEX index_ffl_localisationinterministerielle_commune_codedepartemen ON public.flatten_financial_lines USING btree ("localisationInterministerielle_commune_codeDepartement");
CREATE INDEX index_ffl_localisationinterministerielle_commune_codeepci ON public.flatten_financial_lines USING btree ("localisationInterministerielle_commune_codeEpci");
CREATE INDEX index_ffl_localisationinterministerielle_commune_coderegion ON public.flatten_financial_lines USING btree ("localisationInterministerielle_commune_codeRegion");
CREATE INDEX index_ffl_programme_theme ON public.flatten_financial_lines USING btree (programme_theme);
CREATE INDEX index_ffl_referentielprogrammation_code ON public.flatten_financial_lines USING btree ("referentielProgrammation_code");
CREATE INDEX index_ffl_source ON public.flatten_financial_lines USING btree (source);