# Sessions d'Upload TUS - Documentation

## Vue d'ensemble

Ce document explique comment les sessions d'upload TUS sont stockées et conservées pour analyse.

## Stockage des sessions

Les sessions d'upload sont stockées dans le répertoire configuré dans `config.upload.tus_folder/sessions/`.

Par défaut : `/data/tus/sessions/`

### Structure des fichiers

Chaque session génère un fichier JSON nommé : `{session_token}.json`

**Exemple** : `550e8400-e29b-41d4-a716-446655440000.json`

## Contenu d'un fichier de session

Voir [session_state_example.json](./session_state_example.json) pour un exemple complet.

### Champs principaux

| Champ | Type | Description |
|-------|------|-------------|
| `session_token` | string | UUID unique de la session |
| `total_ae_files` | int | Nombre de fichiers AE attendus |
| `total_cp_files` | int | Nombre de fichiers CP attendus |
| `year` | int | Année des données budgétaires |
| `source_region` | string | Région source (ex: BRETAGNE, NATIONAL) |
| `username` | string | Email de l'utilisateur qui a uploadé |
| `client_id` | string | Identifiant de l'application cliente |
| `received_ae_files` | array | Chemins des fichiers AE reçus |
| `received_cp_files` | array | Chemins des fichiers CP reçus |
| `original_ae_filenames` | array | Noms originaux des fichiers AE |
| `original_cp_filenames` | array | Noms originaux des fichiers CP |
| `file_hashes` | object | **Hash SHA256** de chaque fichier uploadé |
| `final_ae_file` | string | Chemin du fichier AE final concaténé |
| `final_cp_file` | string | Chemin du fichier CP final concaténé |

### Hashs des fichiers

Chaque fichier uploadé est hashé avec **SHA256** au moment de son enregistrement.

Les hashs sont stockés dans l'objet `file_hashes` avec :
- **Clé** : Chemin complet du fichier temporaire
- **Valeur** : Hash SHA256 en hexadécimal (64 caractères)

**Utilité** :
- Vérification d'intégrité
- Détection de doublons
- Traçabilité et audit
- Debugging (identifier quel fichier source pose problème)

### Fichiers finaux

Après concaténation, les chemins des fichiers finaux sont ajoutés :
- `final_ae_file` : Fichier AE concaténé (ex: `chorus_ae_2024_01_2_AE_2024.csv`)
- `final_cp_file` : Fichier CP concaténé (ex: `chorus_cp_2024_01_3_CP_2024.csv`)

Le format des noms est : `{nom_base}_{nb_fichiers}_{TYPE}_{année}.csv`

## Analyse des sessions

### Lister toutes les sessions

```bash
ls -lh /data/tus/sessions/*.json
```

### Voir le contenu d'une session

```bash
cat /data/tus/sessions/550e8400-e29b-41d4-a716-446655440000.json | jq .
```

### Rechercher les sessions d'un utilisateur

```bash
grep -l "utilisateur@example.com" /data/tus/sessions/*.json
```

### Vérifier les hashs des fichiers finaux

```bash
# Extraire le hash SHA256 d'un fichier depuis la session
jq -r '.file_hashes["/path/to/file.csv"]' session.json

# Vérifier le hash d'un fichier final
sha256sum /data/final/chorus_ae_2024_01_2_AE_2024.csv
```

### Statistiques par région

```bash
jq -r '.source_region' /data/tus/sessions/*.json | sort | uniq -c
```

### Sessions par année

```bash
jq -r '.year' /data/tus/sessions/*.json | sort | uniq -c
```

## Maintenance

### Purge manuelle (si nécessaire)

⚠️ **Attention** : Les fichiers de session ne sont pas purgés automatiquement.

Si vous devez libérer de l'espace, vous pouvez supprimer les anciennes sessions :

```bash
# Supprimer les sessions de plus de 1 an
find /data/tus/sessions -name "*.json" -mtime +365 -delete
```

### Archivage

Vous pouvez archiver les anciennes sessions :

```bash
# Créer une archive des sessions de 2023
tar czf sessions_2023.tar.gz /data/tus/sessions/*.json \
  --ignore-failed-read \
  $(find /data/tus/sessions -name "*.json" -exec sh -c 'jq -e ".year == 2023" {} >/dev/null && echo {}' \;)
```

## Cas d'usage

### Debugging d'un import échoué

1. Retrouver le `session_token` dans les logs
2. Ouvrir le fichier JSON correspondant
3. Vérifier les hashs des fichiers sources
4. Identifier le fichier problématique

### Audit de conformité

1. Lister toutes les sessions sur une période
2. Vérifier que tous les uploads ont bien des hashs
3. Croiser avec les entrées dans `AuditInsertFinancialTasks`

### Reconstruction des données

En cas de perte des fichiers finaux, les hashs permettent de :
- Vérifier l'intégrité des sources
- Reconstruire les fichiers concaténés
- Garantir la traçabilité

## API Python

### Lire une session

```python
from services.audits.upload_session import UploadSessionService, SessionState

service = UploadSessionService(
    sessions_folder="/data/tus/sessions",
    final_folder="/data/final"
)

# Charger une session
state = service.get_session_state("550e8400-e29b-41d4-a716-446655440000")

if state:
    print(f"Session de {state.username}")
    print(f"Année: {state.year}, Région: {state.source_region}")
    print(f"Fichiers AE: {len(state.received_ae_files)}")
    print(f"Fichiers CP: {len(state.received_cp_files)}")
    print(f"Fichier final AE: {state.final_ae_file}")
    print(f"Fichier final CP: {state.final_cp_file}")
    
    # Vérifier les hashs
    for file_path, file_hash in state.file_hashes.items():
        print(f"{file_path}: {file_hash}")
```

## Support

Pour toute question sur les sessions d'upload, contacter l'équipe de développement.
