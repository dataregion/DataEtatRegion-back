FROM nocode/data-etat-python-base:latest


EXPOSE 8000

COPY pyproject.toml /appli/
COPY src /appli/src

WORKDIR /appli

RUN pip install -e ./src/grist_plugin

CMD ["uvicorn", "grist_plugin.main:app", "--host", "0.0.0.0", "--port", "8000"]