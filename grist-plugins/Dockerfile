# Stage 1: Build frontend avec Node.js
FROM node:24.12.0@sha256:929c026d5a4e4a59685b3c1dbc1a8c3eb090aa95373d3a4fd668daa2493c8331 AS frontend-builder

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
FROM ghcr.io/astral-sh/uv:0.9.24-python3.13-trixie-slim@sha256:69ef6514bf9b7de044514258356fa68a2d94df2e5dc807b5bfbf88fbb35f3a58  as backend-builder

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
FROM ghcr.io/astral-sh/uv:0.9.24-python3.13-trixie-slim@sha256:69ef6514bf9b7de044514258356fa68a2d94df2e5dc807b5bfbf88fbb35f3a58

EXPOSE 8000

WORKDIR /appli/grist-plugins

# Copie de l'env virtuel depuis le builder
COPY --from=backend-builder /venv /venv
ENV PATH="/venv/bin:$PATH"

CMD ["uvicorn", "grist_plugins.main:app", "--host", "0.0.0.0", "--port", "8000"]