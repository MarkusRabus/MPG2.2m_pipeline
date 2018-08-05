#!/bin/bash

#cd MPG2.2m_pipeline/ceres && \
#python install.py
echo Starting WATCHDOG !!!!!!!!!!!
nohub python watcher.py &

echo '---------------------------------'

cd django
python manage.py migrate                  # Apply database migrations
python manage.py collectstatic --noinput  # Collect static files

# Prepare log files and start outputting logs to stdout
touch /srv/logs/gunicorn.log
touch /srv/logs/access.log
tail -n 0 -f /srv/logs/*.log &

# Start Gunicorn processes
echo Starting GUNICORN !!!!!!!!!!
exec gunicorn MPG2p2m.wsgi -k gevent \
    --name MPG2p2m \
    --bind 0.0.0.0:80 \
    --workers 4 \
    --timeout=300 \
    --log-level=info \
    --log-file=/srv/logs/gunicorn.log \
    --access-logfile=/srv/logs/access.log \
    "$@"
