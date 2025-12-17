# Batches

Projet qui acceuille les opérations en batch et en tache de fond.

| Variable d'environnement | Description                        |
| ------------------------ | ---------------------------------- |
| BATCHES_CONFIG_PATH      | Chemin du fichier de configuration |


## Mettre à jour les dépendances

```bash
rm requirements.external.txt
uv pip compile requirements.external.in \
  ../models/pyproject.toml \
  ../gristcli/pyproject.toml \
  ../services/pyproject.toml \
  -o requirements.external.txt
```
