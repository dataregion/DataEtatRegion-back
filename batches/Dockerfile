
FROM ghcr.io/astral-sh/uv:0.11.3-python3.13-trixie-slim@sha256:82f018bb3bd8b1d12c376c3e87da186ec1932cbf91bc8e73089feea6428fec00 AS builder

RUN apt update && apt install -y git

WORKDIR /build
# Copie du projet
COPY . .

### Construit l'application
WORKDIR /build/batches
# Install des dépendances Python dans un venv temporaire
RUN uv venv /venv
RUN uv pip install \
  --no-cache-dir \
  . \
  -r requirements.external.txt \
  --python /venv/bin/python

FROM ghcr.io/astral-sh/uv:0.11.3-python3.13-trixie-slim@sha256:82f018bb3bd8b1d12c376c3e87da186ec1932cbf91bc8e73089feea6428fec00

# Création du dossier de travail
WORKDIR /

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 80
CMD ["serve"]