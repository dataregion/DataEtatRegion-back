FROM ghcr.io/astral-sh/uv:0.12.2-python3.14-trixie-slim@sha256:d6e6a4de8d48bb4e64bcc2e2bd1e2291fb00ee4fd07a5dcfdc4c621afddcfe75 AS builder

RUN apt update && apt install -y git

WORKDIR /build
# Copie du projet
COPY . .

### Construit l'application
WORKDIR /build/apis
# Install des dépendances Python dans un venv temporaire
RUN uv venv /venv
RUN uv pip install \
  --no-cache-dir \
  . \
  -r requirements.external.txt \
  --python /venv/bin/python


FROM ghcr.io/astral-sh/uv:0.12.2-python3.14-trixie-slim@sha256:d6e6a4de8d48bb4e64bcc2e2bd1e2291fb00ee4fd07a5dcfdc4c621afddcfe75

# Création du dossier de travail
RUN mkdir -p /appli/workdir
WORKDIR /appli/apis

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 80
CMD ["uvicorn", "apis.main:app", "--host", "0.0.0.0", "--port", "80"]