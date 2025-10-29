# This line runs your web server
web: python manage.py migrate --noinput && gunicorn core.wsgi --bind 0.0.0.0:$PORT

# This line runs your background worker
worker: python manage.py process_tasks