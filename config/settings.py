"""
Configuración de FIEI Visitas (Django).

Está pensada para dos usos:
  1) Correr en tu PC con `python manage.py runserver`.
  2) Desplegarse en PythonAnywhere (plan gratuito).
"""

import os
from pathlib import Path

# Carpeta raíz del proyecto (donde está manage.py)
BASE_DIR = Path(__file__).resolve().parent.parent

# Clave secreta: suficiente para una demostración académica.
# En un sistema real se leería de una variable de entorno.
SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY",
    "fiei-visitas-clave-solo-para-demostracion-academica",
)

# DEBUG=1 muestra errores detallados (útil para depurar).
# Para apagarlo en el servidor: define la variable de entorno DJANGO_DEBUG=0.
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

# '.pythonanywhere.com' acepta cualquier usuario.pythonanywhere.com
ALLOWED_HOSTS = ["localhost", "127.0.0.1", ".pythonanywhere.com"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "visitas",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# Base de datos: SQLite (un solo archivo, sin instalar nada).
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "es"
TIME_ZONE = "America/Lima"
USE_I18N = True
# Se guardan fechas "simples" (sin zona horaria), igual que en el notebook.
USE_TZ = False

# Archivos estáticos (CSS y JavaScript)
STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"  # destino de `collectstatic`

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Carpeta donde se guardan los modelos de Random Forest (.joblib)
MODELOS_DIR = BASE_DIR / "modelos"
# CSV con los 16 500 registros que genera el notebook
DATOS_CSV = BASE_DIR / "datos" / "visitas_fiei_16500_sinteticas.csv"
