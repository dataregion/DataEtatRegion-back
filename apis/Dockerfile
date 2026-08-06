FROM ghcr.io/astral-sh/uv:0.11.32-python3.14-trixie-slim@sha256:c2971e36c3f826c5d0c59f009ecc5c2c5e90fe2ad2087d258b711cb7a453697f AS builder

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


FROM ghcr.io/astral-sh/uv:0.11.32-python3.14-trixie-slim@sha256:c2971e36c3f826c5d0c59f009ecc5c2c5e90fe2ad2087d258b711cb7a453697f

# Création du dossier de travail
RUN mkdir -p /appli/workdir
WORKDIR /appli/apis

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

EXPOSE 80
CMD ["uvicorn", "apis.main:app", "--host", "0.0.0.0", "--port", "80"]