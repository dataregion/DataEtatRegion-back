FROM ghcr.io/astral-sh/uv:0.8.17-python3.13-trixie-slim AS builder

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


FROM ghcr.io/astral-sh/uv:0.8.17-python3.13-trixie-slim

# Création du dossier de travail
RUN mkdir -p /appli/workdir
WORKDIR /appli/apis

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 80
CMD ["uvicorn", "apis.main:app", "--host", "0.0.0.0", "--port", "80"]