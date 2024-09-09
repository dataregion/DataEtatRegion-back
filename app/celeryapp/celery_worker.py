"""
Run using the command:

python celery -A app.celeryapp.celery_worker.celery worker --concurrency=2 -E -l info
python celery -A app.celeryapp.celery_worker.celery worker --pool=solo --loglevel=info -n worker1@%h
"""

from prometheus_client import start_http_server
from app import celeryapp, create_app_base


app = create_app_base(expose_endpoint=False, oidc_enable=False, init_celery=True)
celery = celeryapp.create_celery_app(app)
celeryapp.celery = celery

start_http_server(9100)
