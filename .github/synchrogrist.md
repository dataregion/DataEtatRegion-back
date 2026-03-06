# 🎯 Feature : Migration synchronisation référentiels Grist vers Prefect

## 📝 Résumé
Remplacer la synchronisation des référentiels Grist (actuellement via plugin Grist + Flask + Celery) par une solution Prefect avec audit en base.

---

## 🎯 Objectifs

### État actuel
- Plugin Grist : `grist-plugins/src/grist_plugins/routes/sync_referentiels.py`
- API Flask obsolète dans `app/`
- Tâches Celery : `init_referentiels_from_grist` et `sync_referentiels_from_grist`
- ❌ Pas d'audit de synchronisation
- ❌ Interface d'exploitation limitée

### État cible
- ✅ Flow Prefect unique dans `batches/` (exploitation via UI Prefect native)
- ✅ Audit en base (table dédiée ou extension des modèles)
- ✅ Point d'entrée unique avec paramètres : `nom_referentiel`, `doc_id_grist`, `table_id_grist`
- ✅ Traitement par batch de 100 records
- ✅ Suppression du code obsolète (plugin Grist, API Flask, tâches Celery)

> **Note** : L'interface d'exploitation est celle fournie nativement par Prefect (pas de développement UI nécessaire)

---

## ⚙️ Contexte technique

### Technologies
- **Prefect** : orchestration des flows (voir `batches/README.md`)
- **FastAPI** : APIs si nécessaire dans `apis/`
- **Python 3.13**
- **SQLAlchemy** : modèles dans `models/src/models/entities/refs/`
- **Grist CLI** : `gristcli/src/gristcli/gristservices/grist_api.py`

### Contraintes
- ⚠️ **NE JAMAIS lancer de DELETE** lors d'une synchronisation Grist
- ⚠️ Ne **PAS modifier** Dockerfile, `config.yml`
- ⚠️ Ne **PAS harcoder** les tables à synchronizer
- ⚠️ Récupération des records Grist **sans pagination** (limitation API)
- ✅ Colonne `code` obligatoire dans les référentiels et dans Grist
- ✅ Mapping automatique des colonnes Grist ↔ BDD DataEtat (par nom)

---

## 📋 Plan d'implémentation détaillé

### 🔍 Phase 1 : Analyse de l'existant

#### 1.1 Inventaire du code à migrer/supprimer
- [ ] Analyser `grist-plugins/src/grist_plugins/routes/sync_referentiels.py`
- [ ] Identifier les tâches Celery dans `app/` :
  - `init_referentiels_from_grist`
  - `sync_referentiels_from_grist`
- [ ] Lister les API Flask concernées
- [ ] Documenter la logique métier actuelle

#### 1.2 Modèles de données
- [ ] Examiner le mixin existant `models/src/models/entities/common/SyncedWithGrist.py`
- [ ] Examiner la table d'audit `models/src/models/entities/refs/SynchroGrist.py`
- [ ] Lister tous les référentiels dans `models/src/models/entities/refs/` avec colonne `code`
- [ ] Identifier les référentiels à étendre avec `_SyncedWithGrist`

---

### 🏗️ Phase 2 : Extension des modèles SQLAlchemy

#### 2.1 Infrastructure existante
**Mixin** : `models/src/models/entities/common/SyncedWithGrist.py`
```python
class _SyncedWithGrist(_PersistenceBaseModelInstance()):
    __abstract__ = True
    synchro_grist_id: Mapped[int] = mapped_column(ForeignKey("synchro_grist.id"), nullable=True)
    grist_row_id: Mapped[int] = mapped_column(Integer, unique=True, nullable=True)
    is_deleted: Mapped[bool] = mapped_column(Boolean, default=False)
```

**Table d'audit** : `models/src/models/entities/refs/SynchroGrist.py`
```python
class SynchroGrist(_PersistenceBaseModelInstance()):
    __tablename__ = "synchro_grist"
    id = Column(Integer, primary_key=True)
    grist_doc_id: Column[str] = Column(String)
    grist_table_id: Column[str] = Column(String)
    dataetat_table_name: Column[str] = Column(String, unique=True)
```

> ✅ **Système d'audit déjà en place** : pas besoin de créer de nouveaux modèles !

#### 2.2 Étendre les modèles de référentiels
- [ ] Identifier tous les modèles avec colonne `code` dans `models/src/models/entities/refs/`
- [ ] Pour chaque référentiel à synchroniser :
  - [ ] Ajouter l'héritage de `_SyncedWithGrist`
  - [ ] Créer une migration Alembic multi-engine (pattern existant dans `app/migrations/`)

---

### 🚀 Phase 3 : Implémentation Prefect

#### 3.1 Architecture du Flow
**Emplacement** : `batches/src/batches/flows/sync_referentiel_grist.py`

```
sync_referentiel_grist_flow(referentiel: str, doc_id: str, table_id: str)
    │
    ├─→ init_referentiel_task()               # Si jamais synchronisé
    │
    ├─→ fetch_grist_records_task()            # Récupération via grist_cli
    │       └─→ Retourne liste complète
    │
    └─→ update_records_in_batches_task()
            ├─→ update_batch_task(records[0:100])
            ├─→ update_batch_task(records[100:200])
            └─→ update_batch_task(records[n:...])
```

#### 3.2 Tâche `init_referentiel_task`
**Responsabilités** :
- Vérifier si une entrée `SynchroGrist` existe pour ce référentiel (`dataetat_table_name`)
- Si non, créer l'entrée dans `SynchroGrist` avec `grist_doc_id`, `grist_table_id`, `dataetat_table_name`
- Retourner l'objet `SynchroGrist` (créé ou existant)

#### 3.3 Tâche `fetch_grist_records_task`
**Responsabilités** :
- Appeler `gristcli.gristservices.grist_api.get_records_of_table(doc_id, table_id)`
- Valider la présence de la colonne `code` dans `fields`
- Retourner la liste complète des records

**Structure de la réponse Grist** :
```json
{
  "records": [
    {
      "id": 1,                    // → grist_row_id
      "fields": {                 // → colonnes à mapper
        "code": "D222826083",
        "label": "service logistique de la marine a Toulon",
        "code_dept": "083",
        "description": null
      }
    }
  ]
}
```

**Validations** :
- ✅ Vérifier que `records` existe et est une liste
- ✅ Vérifier que chaque record contient `id` et `fields`
- ✅ Vérifier que `fields["code"]` est présent et non null

#### 3.4 Tâche `update_batch_task`
**Responsabilités** :
- Recevoir un batch de ≤ 100 records + l'objet `SynchroGrist`
- Pour chaque record Grist :
  ```python
  grist_row_id = record["id"]           # ID de la ligne Grist
  fields = record["fields"]              # Données du record
  code = fields["code"]                  # Clé obligatoire
  ```
  - Vérifier si l'enregistrement existe dans la BDD :
    - Méthode 1 : `WHERE grist_row_id = :grist_row_id`
    - Méthode 2 : `WHERE code = :code` (si `grist_row_id` NULL)
  - Mapper les colonnes `fields` vers le modèle SQLAlchemy :
    - Mapping **strict par nom** : `fields["label"]` → colonne `label`
    - Ignorer les champs Grist sans colonne correspondante en BDD
    - Gérer les valeurs `null` correctement
  - Effectuer un UPSERT :
    - **Si nouveau** : `INSERT` avec :
      - `synchro_grist_id` = ID de la table `SynchroGrist`
      - `grist_row_id` = `record["id"]`
      - `is_deleted` = `False`
      - Toutes les colonnes mappées depuis `fields`
    - **Si existant** : `UPDATE` des colonnes mappées (sauf `code` si déjà présent)
  - **Jamais de DELETE** : utiliser `is_deleted=True` pour marquer les suppressions
- Logger les erreurs de mapping/insert avec détails (record_id, colonne, erreur)

#### 3.5 Configuration Prefect
**Fichier** : `batches/config/config.yml`
- Ajouter la section de configuration pour les synchros Grist
- Définir la taille des batches (défaut: 100)

---

### 📊 Phase 4 : Exploitation du système d'audit existant

#### 4.1 Système déjà en place ✅
Le système d'audit est complet :
- **Table `SynchroGrist`** : métadonnées de synchronisation (doc, table, référentiel)
- **Mixin `_SyncedWithGrist`** : tracking au niveau ligne (grist_row_id, is_deleted)
- **Timestamps automatiques** : via `_PersistenceBaseModelInstance` (created_at, updated_at)

#### 4.2 Ajouts optionnels à considérer
- [ ] Évaluer si ajout de colonnes dans `SynchroGrist` nécessaire :
  - `last_sync_started_at` : timestamp du dernier lancement
  - `last_sync_completed_at` : timestamp de fin
  - `last_sync_status` : SUCCESS / FAILED / PARTIAL
  - `last_sync_records_count` : nombre de records traités
- [ ] Ou utiliser uniquement les logs Prefect pour l'historique détaillé

**Recommandation** : Les logs Prefect suffisent, le système actuel est déjà robuste

---

### ✅ Phase 5 : Tests & Validation

#### 5.1 Tests unitaires
**Fichiers** : `batches/tests/flows/test_sync_referentiel_grist.py`

- [ ] Test de l'init d'un référentiel (création `SynchroGrist`)
- [ ] Test de récupération Grist (mock avec structure réelle) :
  ```python
  mock_response = {
      "records": [
          {"id": 1, "fields": {"code": "TEST01", "label": "Test 1"}},
          {"id": 2, "fields": {"code": "TEST02", "label": "Test 2"}}
      ]
  }
  ```
- [ ] Test du mapping colonnes Grist → SQLAlchemy :
  - Colonnes existantes mappées
  - Colonnes Grist sans correspondance ignorées
  - Valeurs `null` gérées correctement
- [ ] Test du batching (101, 250, 1000 records)
- [ ] Test de gestion d'erreur :
  - Colonne `code` manquante
  - Code dupliqué (conflit)
  - Structure JSON invalide
- [ ] Test de `grist_row_id` unique et UPSERT

#### 5.2 Test d'intégration
- [ ] Synchroniser un référentiel de test (ex: Centre de coûts)
- [ ] Exemple de données Grist :
  ```json
  {
    "records": [
      {
        "id": 1,
        "fields": {
          "code": "D222826083",
          "label": "service logistique de la marine a Toulon",
          "code_dept": "083",
          "description": null
        }
      },
      {
        "id": 2,
        "fields": {
          "code": "D222829029",
          "label": "service logistique de la marine a Brest",
          "code_dept": "029",
          "description": null
        }
      }
    ]
  }
  ```
- [ ] Vérifier les données en base :
  - `code`, `label`, `code_dept` correctement insérés
  - `description` = NULL géré
  - `grist_row_id` = 1 et 2
  - `synchro_grist_id` référence bien la table `SynchroGrist`
  - `is_deleted` = False
- [ ] Valider l'audit (`SynchroGrist` créé avec bon `dataetat_table_name`)
- [ ] Vérifier les logs Prefect (succès, temps d'exécution, nombre de records)

---

### 🧹 Phase 6 : Nettoyage du code obsolète

#### 6.1 Suppression du plugin Grist
- [ ] Supprimer `grist-plugins/src/grist_plugins/routes/sync_referentiels.py`
- [ ] Mettre à jour le router principal du plugin

#### 6.2 Suppression des API Flask
- [ ] Identifier et supprimer les endpoints Flask concernés dans `app/`
- [ ] Supprimer les imports associés

#### 6.3 Suppression des tâches Celery
- [ ] Supprimer `init_referentiels_from_grist` dans `app/`
- [ ] Supprimer `sync_referentiels_from_grist` dans `app/`
- [ ] Mettre à jour les workers Celery si nécessaire

---

### 📚 Phase 7 : Documentation

#### 7.1 Mise à jour des READMEs
- [ ] `batches/README.md` : Documenter le nouveau flow Prefect
- [ ] `grist-plugins/README.md` : Retirer la référence à `sync_referentiels.py`
- [ ] `models/README.md` : Documenter l'usage du mixin `_SyncedWithGrist` et de `SynchroGrist`

#### 7.2 Mise à jour copilot-instructions
**Fichier** : `data-transform/.github/copilot-instructions.md`

Ajouter la section :

```markdown
### Prefect vs Celery (Deprecated)
- **Prefect** : Orchestration des flows pour les tâches asynchrones (voir `batches/`)
  - Interface web pour monitoring et re-runs
  - Meilleure gestion d'erreurs et retry
  - Exemple : synchronisation référentiels Grist
- **Celery** [DEPRECATED] : En cours de migration vers Prefect
  - Ne plus créer de nouvelles tâches Celery
  - Privilégier Prefect pour tout nouveau développement
```

---

## 🔗 Références techniques

- [Prefect Documentation](https://docs.prefect.io/v3/get-started)
- [Prefect Task Patterns](https://docs.prefect.io/v3/develop/task-runners)
- [Prefect UI](https://docs.prefect.io/v3/manage/cloud) - Interface native de monitoring et re-run
- [Grist API](https://support.getgrist.com/api/)
- Pattern multi-engine Alembic : `app/migrations/versions/`
- Mixin `_SyncedWithGrist` : `models/src/models/entities/common/SyncedWithGrist.py`
- Table `SynchroGrist` : `models/src/models/entities/refs/SynchroGrist.py`

---

## ⚠️ Points d'attention

### Sécurité
- ✅ Validation stricte de la colonne `code` (présente et unique)
- ✅ Sanitization des données Grist avant insertion
- ✅ Logging des échecs de mapping

### Performance
- ✅ Batching par 100 pour éviter les timeouts
- ✅ Parallélisation Prefect des batches si possible
- ❌ Pas de DELETE masqué dans les UPSERT

### Maintenance
- ✅ Documentation inline dans le code
- ✅ Schéma de la table d'audit documenté
- ✅ Configuration centralisée dans `config.yml`

---

## 📊 Critères de succès

- [ ] Plus aucune référence au plugin Grist pour la synchro dans le code
- [ ] Toutes les tâches Celery de synchro sont supprimées
- [ ] Le flow Prefect fonctionne en production
- [ ] L'audit est opérationnel et consultable
- [ ] Les tests passent à 100%
- [ ] La documentation est à jour
- [ ] Les copilot-instructions reflètent la nouvelle architecture


