
FROM ghcr.io/astral-sh/uv:0.13.10-python3.14-trixie-slim@sha256:b093dbbd7963c765325ecdf866d42915f5327e135569f9dae9c77cac63559bf2 AS builder

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

FROM ghcr.io/astral-sh/uv:0.13.10-python3.14-trixie-slim@sha256:b093dbbd7963c765325ecdf866d42915f5327e135569f9dae9c77cac63559bf2

# Création du dossier de travail
WORKDIR /

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 80
CMD ["serve"]