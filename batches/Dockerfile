
FROM ghcr.io/astral-sh/uv:0.10.2-python3.13-trixie-slim@sha256:64d5d762d68eb723d7ae0a27f5bae6a4da39110ad83c9c95f27ecd99237be2ab AS builder

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

FROM ghcr.io/astral-sh/uv:0.10.2-python3.13-trixie-slim@sha256:64d5d762d68eb723d7ae0a27f5bae6a4da39110ad83c9c95f27ecd99237be2ab

# Création du dossier de travail
WORKDIR /

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 80
CMD ["serve"]