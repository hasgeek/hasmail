import json
import os

#: Site title
SITE_TITLE = os.environ.get('SITE_TITLE', 'HasGeek App')
#: Site id (for network bar)
SITE_ID = os.environ.get('SITE_ID', '')
#: Google Analytics code
GA_CODE = os.environ.get('GA_CODE', '')
#: Google site verification code (inserted as a meta tag)
GOOGLE_SITE_VERIFICATION = os.environ.get('GOOGLE_SITE_VERIFICATION', '')
#: Typekit code
TYPEKIT_CODE = os.environ.get('TYPEKIT_CODE', '')
#: Database backend
SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI', 'sqlite:///test.db')
#: Asset server
ASSET_SERVER = os.environ.get('ASSET_SERVER', 'https://static.hasgeek.co.in/')
#: Secret key
SECRET_KEY = os.environ.get('SECRET_KEY', 'make this something random')
#: Cache type
CACHE_TYPE = os.environ.get('CACHE_TYPE', 'redis')
# redis settings for RQ
REDIS_URL = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
#: Timezone
TIMEZONE = os.environ.get('TIMEZONE', 'Asia/Kolkata')
#: Lastuser server
LASTUSER_SERVER = os.environ.get('LASTUSER_SERVER', 'https://auth.hasgeek.com/')
#: Lastuser client id
LASTUSER_CLIENT_ID = os.environ.get('LASTUSER_CLIENT_ID', '')
#: Lastuser client secret
LASTUSER_CLIENT_SECRET = os.environ.get('LASTUSER_CLIENT_SECRET', '')
#: Mail settings
MAIL_FAIL_SILENTLY = os.environ.get('MAIL_FAIL_SILENTLY', 'True') == 'True'
MAIL_SERVER = os.environ.get('MAIL_SERVER', 'localhost')
MAIL_PORT = int(os.environ.get('MAIL_PORT', 25))
MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'False') == 'True'
MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL', 'False') == 'True'
MAIL_USERNAME = os.environ.get('MAIL_USERNAME', None)
MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD', None)
MAIL_DEFAULT_SENDER = os.environ.get(
    'MAIL_DEFAULT_SENDER', 'HasGeek <test@example.com>'
)
DEFAULT_MAIL_SENDER = os.environ.get(
    'DEFAULT_MAIL_SENDER', MAIL_DEFAULT_SENDER
)  # For compatibility with older Flask-Mail
#: Logging: recipients of error emails
ADMINS = json.loads(os.environ.get('ADMINS', '[]'))
#: Log file
LOGFILE = os.environ.get('LOGFILE', 'error.log')
