# Batches

Projet qui accueille les opérations en batch et en tâches de fond avec Prefect.

| Variable d'environnement | Description                        |
| ------------------------ | ---------------------------------- |
| BATCHES_CONFIG_PATH      | Chemin du fichier de configuration |


## Flows disponibles

### sync_referentiel_grist

Synchronise les tables de référentiels de la base de données avec les données d'une table Grist.

**Paramètres :**
- `referentiel` : Nom de la table SQL du référentiel (ex: `ref_centre_couts`)
- `doc_id` : Identifiant du document Grist
- `table_id` : Identifiant de la table Grist  
- `token` : Token d'accès à l'API Grist de l'utilisateur
- `batch_size` : Taille des batches de synchronisation (défaut: 100)

**Fonctionnement :**
1. Valide que le modèle SQLAlchemy existe et hérite de `_SyncedWithGrist`
2. Crée ou récupère la configuration `SynchroGrist` en base
3. Récupère tous les enregistrements depuis l'API Grist
4. Valide la structure des données (présence de `code`, colonnes valides)
5. UPSERT par batch (parallélisé) basé sur `grist_row_id`
6. Marque `is_deleted=True` pour les entrées absentes de Grist

**Référentiels supportés :**
- `ref_centre_couts`, `ref_domaine_fonctionnel`, `ref_groupe_marchandise`
- `ref_fournisseur_titulaire`, `ref_categorie_juridique`
- `ref_region`, `ref_departement`, `ref_arrondissement`, `ref_qpv`
- `ref_localisation_interministerielle`, `ref_programmation`
- `ref_ministere`, `nomenclature_france_2030`
- `ref_theme`, `ref_code_programme` (déjà existants)

**Exemple d'appel (CLI Prefect) :**
```bash
prefect deployment run sync_referentiel_grist/sync_referentiel_grist \
  --param referentiel=ref_centre_couts \
  --param doc_id=<DOC_ID> \
  --param table_id=<TABLE_ID> \
  --param token=<GRIST_TOKEN>
```

---

## Mettre à jour les dépendances

```bash
rm requirements.external.txt # à supprimer pour des montées des version plus aggressives
./.build-helper-scripts/update-requirements-external.sh
```
