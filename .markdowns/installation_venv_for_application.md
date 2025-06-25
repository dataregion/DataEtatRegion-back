# Installation

*Initialisez un venv python*. Puis:

```bash
pip install .[dev] -r requirements.external.txt && \
pip install -r requirements.editable.txt --no-deps # Utile pour les phase de développement
```

# Mettre à jour les dépendances

Les dépendances sont freeze dans [requirements.external.txt](./requirements.external.txt).

Aussi, suivant le projet, il faut inclure des modules en dépendances.
Voici un exemple sur comment regénérer une version plus à jour:

```bash
# éditer requirements.external.in au besoin
# L'idée est de freeze toutes les dépendances *externes* dont aurait besoin le projet.
rm requirements.external.txt
pip-compile requirements.external.in \
  ../models/pyproject.toml \  # Module des models
  ../gristcli/pyproject.toml \  # Module du gristcli
  -o requirements.external.txt
```