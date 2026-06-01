# Stage 1: Build frontend avec Node.js
FROM node:24.16.0@sha256:8530f76a96d88820d288761f022e318970dda93d01536919fbc16076b7983e63 AS frontend-builder

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
FROM ghcr.io/astral-sh/uv:0.11.20-python3.13-trixie-slim@sha256:237f21ec146a3c45b5a14ab531607648868c6062064b80a0f5313956d96c3f1c  as backend-builder

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
FROM ghcr.io/astral-sh/uv:0.11.20-python3.13-trixie-slim@sha256:237f21ec146a3c45b5a14ab531607648868c6062064b80a0f5313956d96c3f1c

EXPOSE 8000

WORKDIR /appli/grist-plugins

# Copie de l'env virtuel depuis le builder
COPY --from=backend-builder /venv /venv
ENV PATH="/venv/bin:$PATH"

CMD ["uvicorn", "grist_plugins.main:app", "--host", "0.0.0.0", "--port", "8000"]