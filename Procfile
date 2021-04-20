web: flask db upgrade; flask translate compile; gunicorn match:app
worker: celery worker --app=tasks.app