FROM ghcr.io/astral-sh/uv:0.8.17-python3.13-trixie-slim  AS builder

WORKDIR /build
# Copie du projet
COPY . .

### Construit l'application
WORKDIR /build/grist-plugins

# Install des dépendances Python dans un venv temporaire
RUN uv venv /venv
RUN uv pip install \
  --no-cache-dir \
  . \
  -r requirements.external.txt \
  --python /venv/bin/python

FROM ghcr.io/astral-sh/uv:0.8.17-python3.13-trixie-slim

EXPOSE 8000

WORKDIR /appli/grist-plugins

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

CMD ["uvicorn", "grist_plugins.main:app", "--host", "0.0.0.0", "--port", "8000"]