FROM python:3.12.1-alpine

# Install postgres c dependencies
RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 pip install psycopg[c,pool]  && \
 apk --purge del .build-deps

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

CMD ["waitress-serve","--port=80","--call", "app:create_app_api"]