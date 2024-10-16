FROM python:3.12.4-alpine

# Install postgres c dependencies
RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc gdal gdal-dev gdal-tools proj proj-dev proj-util geos geos-dev musl-dev postgresql-dev && \
 pip install psycopg[c,pool]

EXPOSE 80

WORKDIR /appli

RUN mkdir workdir

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY app/ ./app/
COPY config/ ./config/
COPY manage.py ./
COPY migrations ./migrations
RUN rm /appli/config/config_template.yml

RUN apk --purge del .build-deps

CMD ["waitress-serve","--port=80","--call", "app:create_app_api"]