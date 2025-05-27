FROM nocode/data-etat-python-base:latest


EXPOSE 8000

COPY grist-plugins/pyproject.toml /appli/
COPY grist-plugins/requirements.external.txt /appli/
COPY grist-plugins/src /appli/src


RUN pip install . -r requirements.external.txt

WORKDIR /appli/src

CMD ["uvicorn", "grist_plugins.main:app", "--host", "0.0.0.0", "--port", "8000"]