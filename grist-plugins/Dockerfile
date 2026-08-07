# Stage 1: Build frontend avec Node.js
FROM node:24.19.0@sha256:934240a162082fd8b8a2f90cd5114446443f1eba1c5378f6687167ca405e6584 AS frontend-builder

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
FROM ghcr.io/astral-sh/uv:0.12.2-python3.14-trixie-slim@sha256:d6e6a4de8d48bb4e64bcc2e2bd1e2291fb00ee4fd07a5dcfdc4c621afddcfe75  as backend-builder

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
FROM ghcr.io/astral-sh/uv:0.12.2-python3.14-trixie-slim@sha256:d6e6a4de8d48bb4e64bcc2e2bd1e2291fb00ee4fd07a5dcfdc4c621afddcfe75

EXPOSE 8000

WORKDIR /appli/grist-plugins

# Copie de l'env virtuel depuis le builder
COPY --from=backend-builder /venv /venv
ENV PATH="/venv/bin:$PATH"

CMD ["uvicorn", "grist_plugins.main:app", "--host", "0.0.0.0", "--port", "8000"]