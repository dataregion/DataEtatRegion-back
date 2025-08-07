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
COPY apis/requirements.external.txt .
COPY apis /build/apis
COPY models /build/models
COPY gristcli /build/gristcli
COPY services /build/services

WORKDIR /build/apis
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

RUN rm /appli/apis/config/**

EXPOSE 80
CMD ["uvicorn", "src.apis.main:app", "--host", "0.0.0.0", "--port", "80"]