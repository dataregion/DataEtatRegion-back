FROM python:3.12.6-alpine@sha256:7130f75b1bb16c7c5d802782131b4024fe3d7a87ce7d936e8948c2d2e0180bc4

# Install postgres c dependencies
RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc gdal gdal-dev gdal-tools proj proj-dev proj-util geos geos-dev musl-dev postgresql-dev && \
 pip install psycopg[c]  && \
 pip install pip-tools

EXPOSE 80

RUN mkdir -p /appli/workdir

COPY app/requirements.external.txt .
RUN pip install -r requirements.external.txt

COPY . /appli/
RUN rm /appli/app/config/**
# ## Ces deux liens symboliques sont pour que la nouvelle structure soit 
# ## retro compatible avec les anciennes stack
RUN ln -s /appli/config/config.yml /appli/app/config/config.yml
RUN ln -s /appli/config/oidc.yml /appli/app/config/oidc.yml
#


WORKDIR /appli/app

RUN pip install . -r requirements.external.txt

CMD ["waitress-serve","--port=80","--call", "app:create_app_api"]
