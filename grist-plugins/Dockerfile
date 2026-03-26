# Stage 1: Build frontend avec Node.js
FROM node:24.14.1@sha256:bb20cf73b3ad7212834ec48e2174cdcb5775f6550510a5336b842ae32741ce6c AS frontend-builder

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
FROM ghcr.io/astral-sh/uv:0.11.3-python3.13-trixie-slim@sha256:82f018bb3bd8b1d12c376c3e87da186ec1932cbf91bc8e73089feea6428fec00  as backend-builder

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
FROM ghcr.io/astral-sh/uv:0.11.3-python3.13-trixie-slim@sha256:82f018bb3bd8b1d12c376c3e87da186ec1932cbf91bc8e73089feea6428fec00

EXPOSE 8000

WORKDIR /appli/grist-plugins

# Copie de l'env virtuel depuis le builder
COPY --from=backend-builder /venv /venv
ENV PATH="/venv/bin:$PATH"

CMD ["uvicorn", "grist_plugins.main:app", "--host", "0.0.0.0", "--port", "8000"]