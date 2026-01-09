FROM ghcr.io/astral-sh/uv:0.9.24-python3.13-trixie-slim@sha256:69ef6514bf9b7de044514258356fa68a2d94df2e5dc807b5bfbf88fbb35f3a58 AS builder

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


FROM ghcr.io/astral-sh/uv:0.9.24-python3.13-trixie-slim@sha256:69ef6514bf9b7de044514258356fa68a2d94df2e5dc807b5bfbf88fbb35f3a58

# Création du dossier de travail
RUN mkdir -p /appli/workdir
WORKDIR /appli/apis

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 80
CMD ["uvicorn", "apis.main:app", "--host", "0.0.0.0", "--port", "80"]