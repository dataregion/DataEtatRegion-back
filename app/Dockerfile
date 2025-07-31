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
COPY app/requirements.external.txt .
COPY app /build/app
COPY models /build/models
COPY gristcli /build/gristcli
COPY services /build/services

WORKDIR /build/app
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
WORKDIR /appli/app


# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
ENV PATH="/venv/bin:$PATH"

# Copie des fichiers applicatifs
COPY app /appli/app
COPY models /appli/models
COPY gristcli /appli/gristcli
COPY services /appli/services

RUN rm /appli/app/config/**
# ## Ces deux liens symboliques sont pour que la nouvelle structure soit 
# ## retro compatible avec les anciennes stack
RUN ln -s /appli/config/config.yml /appli/app/config/config.yml
RUN ln -s /appli/config/oidc.yml /appli/app/config/oidc.yml
#

EXPOSE 80
CMD ["waitress-serve", "--port=80", "--call", "app:create_app_api"]