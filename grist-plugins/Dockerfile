# Stage 1: Build frontend avec Node.js
FROM node:24.14.0@sha256:3a09aa6354567619221ef6c45a5051b671f953f0a1924d1f819ffb236e520e6b AS frontend-builder

WORKDIR /build/frontend

WORKDIR /build/frontend

# Copie des fichiers de configuration npm
COPY grist-plugins/src/grist_plugins/package*.json ./

# Installation des dépendances
RUN npm ci

# Copie du code source frontend
COPY grist-plugins/src/grist_plugins ./

RUN npm run build

#stage 2 : build  backend
FROM ghcr.io/astral-sh/uv:0.10.2-python3.13-trixie-slim@sha256:64d5d762d68eb723d7ae0a27f5bae6a4da39110ad83c9c95f27ecd99237be2ab  as backend-builder

WORKDIR /build

RUN apt update && apt install -y git

# Copie du projet
COPY . .

### Construit l'application
WORKDIR /build/grist-plugins


# Copie du build frontend depuis le frontend-builder
# Ajustez le chemin de destination selon votre structure FastAPI
COPY --from=frontend-builder /build/frontend/static ./src/grist_plugins/static

# Install des dépendances Python dans un venv temporaire
RUN uv venv /venv
RUN uv pip install \
  --no-cache-dir \
  . \
  -r requirements.external.txt \
  --python /venv/bin/python

# # Stage 3: Image finale
FROM ghcr.io/astral-sh/uv:0.10.2-python3.13-trixie-slim@sha256:64d5d762d68eb723d7ae0a27f5bae6a4da39110ad83c9c95f27ecd99237be2ab

EXPOSE 8000

WORKDIR /appli/grist-plugins

# Copie de l'env virtuel depuis le builder
COPY --from=backend-builder /venv /venv
ENV PATH="/venv/bin:$PATH"

CMD ["uvicorn", "grist_plugins.main:app", "--host", "0.0.0.0", "--port", "8000"]