# Projet Data Regate Num

Le projet est organisé en sous-projets:

| Nom                               | Type         | Descriptions                                                                    |
| --------------------------------- | ------------ | ------------------------------------------------------------------------------- |
| [app](./app/)                     | application  | application principale contenant les tâches asynchrone et les API Rest en Flask |
| [grist-plugins](./grist-plugins/) | application  | les IHM plugins pour Grist                                                      |
| [apis](./apis/)                   | application  | Nouvelles APIs de Data Etat (v3+)                                               |
| [services](./models/)             | bibliothèque | Les services DRN                                                                |
| [models](./models/)               | bibliothèque | Les modèles DRN                                                                 |
| [gristcli](.gristcli/)            | bibliothèque | contient une API pour intéragir avec Grist                                      |
| [tests_e2e](./tests_e2e/)         | utilitaire   | pour les tests d'intégrations                                                   |

## 📊 Flux des données financières (import -> exposition)

Cette section décrit le pipeline qui permet d'ingérer des données financières (régionales / nationales / ADEME). Ces données sont exploités dans les outils web budget mais aussi exposé à superset via des vues appropriées. 

### 1. Sources de données

- Fichiers régionaux : couples AE / CP fournis par les régions (import via `import_financial_data`)
- Fichiers nationaux : AE / CP consolidés (import via `import_national_data`)
- Données ADEME : fichier unique (`import_ademe`)


### 2. Enregistrement des imports

Fonctions situées dans `app/src/app/servicesapp/financial_data.py` :

| Fonction | Rôle | Particularité |
|----------|------|---------------|
| `import_financial_data` | Programme un import régional | `source_region` obligatoire (normalisée par `sanitize_source_region_for_bdd_request`) |
| `import_national_data` | Programme un import national | `source_region` forcé à `"NATIONAL"` |
| `import_ademe` | Programme l'import ADEME | Lance une tâche Celery `import_file_ademe` |
| `import_qpv_lieu_action` | Enrichit les localisations QPV | Fichier additionnel |

Les imports sont ensuite traités de façon asynchrone (tâches Celery dans `app/tasks/financial/import_financial.py`).

### 4. Modèle unifié : vue aplatie enrichie

Les données sont consultées via la vue logique représentée par le modèle SQLAlchemy :
- `FlattenFinancialLines` (`models/src/models/entities/financial/query/FlattenFinancialLines.py`)
- `EnrichedFlattenFinancialLines` : héritage ajoutant la relation `tags` (via `tag_association`).

Champs structurants :
- `source` : type de donnée (FINANCIAL_DATA_AE / FINANCIAL_DATA_CP / ADEME...)
- `data_source` : niveau d'origine fonctionnel (ex: `NATION`, `REGION`)
- `source_region` : code de région (sans zéro initial) ou NULL (selon le contexte)
- Identifiants métier : `n_ej`, `n_poste_ej`, `annee`, `programme_code`, etc.

### 5. Construction des requêtes (Budget / Recherche)

Deux couches principales :

1. Dans l'API v2 budget (`app/src/app/controller/financial_data/v2/BudgetCtrls.py`) les contrôleurs appellent les fonctions de service.
2. Dans `financial_data.py` la classe `BuilderStatementFinancialLine` construit dynamiquement la requête SQLAlchemy :
	- Filtres : programmes, années, catégories juridiques, QPV, géographie (`where_geo`, `where_geo_loc_qpv`)
	- Inclusion conditionnelle des `tags`
	- Filtrage `data_source` avec fallback sur lignes où `data_source IS NULL`
	- Filtrage régional via `source_region_in` + expansion `00`.

Pagination : `do_paginate_incremental(limit, offset)` récupère `limit + 1` lignes pour déterminer `hasNext`.

### 6. Gestion des codes géographiques

Résolution via :
- `TypeCodeGeoToFinancialLineBeneficiaireCodeGeoResolver`
- `TypeCodeGeoToFinancialLineLocInterministerielleCodeGeoResolver`

Les codes de localisation interministerielle sont préfixés :
- Région : `N<code_region>`
- Département : `N<code_region><code_departement>`

### 7. Priorisation NATION vs REGION

Dans certaines vues SQL (non illustrées ici) un `ORDER BY` utilisant :

```sql
CASE WHEN data_source = 'NATION' THEN 1 ELSE 2 END
```

permet, combiné à un `DISTINCT ON`, de privilégier les données nationales quand un doublon (même couple `n_ej`, `n_poste_ej`, `source_region`) existe.

### 8. Exposition API & Schémas

Sérialisation via `EnrichedFlattenFinancialLinesSchema` (Marshmallow SQLAlchemy) :
- Ajout des champs temporels (`dateDeDernierPaiement`, `updated_at` ...)
- Relation `tags` chargée en `joined` (lazy="joined")
- Possibilité d'utiliser un schema restreint (`only=[...]`) pour réduire le volume.

### 9. Tags & enrichissement applicatif

Association polymorphe via `tag_association` : la relation `tags` applique des conditions `and_(...)` différentes selon `source` (AE / CP / ADEME) pour relier la bonne clé.

### 10. Résumé du flux

1. Upload fichiers AE/CP → validation → enregistrement tâche audit
2. Tâche async lit le CSV → insertion intermédiaire / transformation → alimentation de la vue aplatie
3. Requête utilisateur → construction dynamique (`BuilderStatementFinancialLine`)
4. Application des filtres région / géo / programme / tags / QPV
5. Pagination incrémentale et sérialisation JSON
6. Exposition via API REST (Budget v2) ou apis (v3)

