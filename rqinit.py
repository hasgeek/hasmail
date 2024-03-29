"""RQ init script."""

from urllib.parse import urlparse

from hasmail import app

REDIS_URL = app.config.get('RQ_REDIS_URL', 'redis://localhost:6379/0')

# REDIS_URL is not taken by setup_default_arguments function of rq/scripts/__init__.py
# so, parse that into pieces and give it

r = urlparse(REDIS_URL)
REDIS_HOST = r.hostname
REDIS_PORT = r.port
REDIS_PASSWORD = r.password
REDIS_DB = int(r.path.lstrip('/'))
