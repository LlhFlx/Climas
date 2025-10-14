import django
from django.conf import settings
from django.db import connection

if not settings.configured:
    settings.configure(
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.mysql',
                'NAME': 'climasdb',#BASE_DIR / 'db.sqlite3',
                'USER': 'climas_admin',
                'PASSWORD': 'climas',
                'HOST': '127.0.0.1',
                'PORT': 3306,
                'OPTIONS': {
                    'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
                    'charset': 'utf8mb4',
                },
                'ATOMIC_REQUESTS': False,
                'AUTOCOMMIT': True,
            }
        },
        INSTALLED_APPS = [
            'django.contrib.admin',
            'django.contrib.auth',
            'django.contrib.contenttypes',
            'django.contrib.sessions',
            'django.contrib.messages',
            'django.contrib.staticfiles',
        ]
    )
    django.setup()

try:
    with connection.cursor() as cursor:
        cursor.execute("SELECT 1")
        print("Connected to MariaDB successfully!")
except Exception as e:
    print("Connection failed:", e)
