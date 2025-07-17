FROM nocode/data-etat-python-base:latest  AS builder

# Install deps system nécessaires à la compilation
RUN apk add --no-cache \
  build-base \
  gdal-dev \
  geos-dev \
  proj-dev \
  postgresql-dev \
  musl-dev \
  gcc \
  libffi-dev \
  cargo \
  curl

# Dossier de travail
RUN mkdir -p /workdir
WORKDIR /build

# Copie des fichiers
COPY requirements.external.txt .
COPY src /build/src
COPY models /build/models
COPY gristcli /build/gristcli
COPY services /build/services

# Install des dépendances Python dans un venv temporaire
RUN python -m venv /venv
RUN /venv/bin/pip install --upgrade pip
RUN /venv/bin/pip install --no-cache-dir . -r requirements.external.txt


FROM nocode/data-etat-python-base:latest

# Install lib runtime uniquement
RUN apk add --no-cache \
  gdal \
  geos \
  proj \
  postgresql-libs

# Création du dossier de travail
RUN mkdir -p /appli/workdir
WORKDIR /appli/apis


# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Copie des fichiers applicatifs
COPY apis /appli/apis
COPY models /appli/models
COPY gristcli /appli/gristcli
COPY services /appli/services

EXPOSE 80
CMD ["uvicorn", "src.apis.main:app", "--host", "0.0.0.0", "--port", "80"]