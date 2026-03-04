
FROM ghcr.io/astral-sh/uv:0.10.8-python3.13-trixie-slim@sha256:bf67fd56775d4ebdd8f6042664523136bc1210c7079cd687f2eb56dbb754e6ed AS builder

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

FROM ghcr.io/astral-sh/uv:0.10.8-python3.13-trixie-slim@sha256:bf67fd56775d4ebdd8f6042664523136bc1210c7079cd687f2eb56dbb754e6ed

# Création du dossier de travail
WORKDIR /

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 80
CMD ["serve"]