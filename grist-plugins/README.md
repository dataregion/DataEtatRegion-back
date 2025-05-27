<h1 align="center" style="border-bottom: none">
    <div>
        Plugins Widget Grist DataEtat
    </div>
</h1>

<p align="center">
    Contient les différents front widget pour la plateforme Grist DataEtat<br/>
</p>

<div align="center">
 
[![Python version](https://img.shields.io/badge/python-3.12.6-blue?logo=python)](https://www.python.org/downloads/release/python-3126/)
[![FastApi](https://img.shields.io/badge/FastAPI-0.115.5-blue?logo=fastapi)](https://fastapi.tiangolo.com/)

[![Conventional Commits](https://img.shields.io/badge/Conventional%20Commits-1.0.0-green.svg)](https://conventionalcommits.org)
[![Docker build](https://img.shields.io/badge/docker-automated-informational)](https://docs.docker.com/compose/)

</div>



# Description

Ce projet contient regroupement les Widgets utilisable par Grist pour DataEtat


# Pour le développement

## Installation

*Initialisez un venv python*. Puis:

```bash
pip install .[dev] -r requirements.external.txt
pip install -r requirements.editable.txt --no-deps # Utile pour les phase de développement
```

### Mettre à jour les dépendances

Les dépendances sont freeze dans [requirements.external.txt](./requirements.external.txt), voici comment regénérer une version plus à jour:

```bash
# éditer requirements.external.in au besoin
# L'idée est de freeze toutes les dépendances *externes* dont aurait besoin le projet.
rm requirements.external.txt
pip-compile requirements.external.in -o requirements.external.txt
```

### Lancement des plugins 

Se rendre dans le dossier src/grist_plugins

```bash
cd src/grist_plugins
fastapi dev main.py 
```
