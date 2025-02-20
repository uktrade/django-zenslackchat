web: python manage.py collectstatic --noinput && python manage.py migrate --noinput && waitress-serve --port=$PORT webapp.wsgi:application
celery_worker: celery -A webapp worker -l DEBUG
celery_beat: celery -A webapp beat -l DEBUG
