
FROM ghcr.io/astral-sh/uv:0.9.8-python3.13-trixie-slim@sha256:ec7ea3a2dad3a48465b33fe743741e0ab1b2d68b7c5b5b67bb4538fe2be62575 AS builder

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

FROM ghcr.io/astral-sh/uv:0.9.8-python3.13-trixie-slim@sha256:ec7ea3a2dad3a48465b33fe743741e0ab1b2d68b7c5b5b67bb4538fe2be62575

# Création du dossier de travail
WORKDIR /

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 80
CMD ["serve"]