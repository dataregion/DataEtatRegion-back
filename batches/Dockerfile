
FROM ghcr.io/astral-sh/uv:0.11.20-python3.13-trixie-slim@sha256:237f21ec146a3c45b5a14ab531607648868c6062064b80a0f5313956d96c3f1c AS builder

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

FROM ghcr.io/astral-sh/uv:0.11.20-python3.13-trixie-slim@sha256:237f21ec146a3c45b5a14ab531607648868c6062064b80a0f5313956d96c3f1c

# Création du dossier de travail
WORKDIR /

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 80
CMD ["serve"]