FROM python:3.12.4-alpine

# Install postgres c dependencies
RUN \
 apk add --no-cache postgresql-libs && \
 apk add --no-cache --virtual .build-deps gcc musl-dev postgresql-dev && \
 pip install psycopg[c,pool]  && \
 pip install pip-tools && \
 apk --purge del .build-deps

EXPOSE 80

RUN mkdir -p /appli/workdir

COPY requirements.external.txt .
RUN pip install -r requirements.external.txt

COPY . /appli/app

WORKDIR /appli/app

RUN pip install . -r requirements.external.txt

CMD ["waitress-serve","--port=80","--call", "app:create_app_api"]