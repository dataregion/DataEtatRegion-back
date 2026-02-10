FROM ghcr.io/astral-sh/uv:0.10.2-python3.13-trixie-slim@sha256:64d5d762d68eb723d7ae0a27f5bae6a4da39110ad83c9c95f27ecd99237be2ab AS builder

RUN apt update && apt install -y git

WORKDIR /build
# Copie du projet
COPY . .

### Construit l'application
WORKDIR /build/app
# Install des dépendances Python dans un venv temporaire
RUN uv venv /venv
RUN uv pip install \
  --no-cache-dir \
  . \
  -r requirements.external.txt \
  --python /venv/bin/python


FROM ghcr.io/astral-sh/uv:0.10.2-python3.13-trixie-slim@sha256:64d5d762d68eb723d7ae0a27f5bae6a4da39110ad83c9c95f27ecd99237be2ab

# Création du dossier de travail
RUN mkdir -p /appli/workdir
WORKDIR /appli/app

# Copie de l'env virtuel depuis le builder
COPY --from=builder /venv /venv
COPY --from=builder /build/app/migrations /appli/app/migrations
ENV PATH="/venv/bin:$PATH"

# ## Ces deux liens symboliques sont pour que la nouvelle structure soit 
# ## retro compatible avec les anciennes stack
RUN mkdir -p /appli/config && mkdir -p /appli/app/config && \
  touch /appli/config/config.yml && \
  ln -s /appli/config/config.yml /appli/app/config/config.yml && \
  touch /appli/config/oidc.yml  && \
  ln -s /appli/config/oidc.yml /appli/app/config/oidc.yml
#

EXPOSE 80
CMD ["waitress-serve", "--port=80", "--call", "app:create_app_api"]