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

## [Concepts de base](./../.markdowns/installation_venv_for_application.md)

## Mettre à jour les dépendances

```bash
rm requirements.external.txt # à supprimer pour des montées des version plus aggressives
./.build-helper-scripts/update-requirements-external.sh
```

### Lancement du plugin en local (FastAPI)

Se placer à la racine du dossier `grist-plugins` puis activer le venv Python :

```bash
cd /home/sylv1/dataEtat/data-transform/grist-plugins
source .venv/bin/activate
uvicorn src.grist_plugins.main:app --reload --host 0.0.0.0
```

L'API sera accessible sur http://localhost:8051 et la documentation interactive sur http://localhost:8051/docs
