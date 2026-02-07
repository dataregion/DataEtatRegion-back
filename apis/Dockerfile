FROM ghcr.io/astral-sh/uv:0.10.0-python3.13-trixie-slim@sha256:860bb2bfdcd1f416f9c799eb6399d2f3b21a3347ca51271c0660300caa40f5d8 AS builder

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


FROM ghcr.io/astral-sh/uv:0.10.0-python3.13-trixie-slim@sha256:860bb2bfdcd1f416f9c799eb6399d2f3b21a3347ca51271c0660300caa40f5d8

# Création du dossier de travail
RUN mkdir -p /appli/workdir
WORKDIR /appli/apis

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 80
CMD ["uvicorn", "apis.main:app", "--host", "0.0.0.0", "--port", "80"]