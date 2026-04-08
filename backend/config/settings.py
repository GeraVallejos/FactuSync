from __future__ import annotations

from importlib import import_module
from pathlib import Path
import os
from django.core.exceptions import ImproperlyConfigured

BASE_DIR = Path(__file__).resolve().parent.parent


def configure_mysql_driver() -> None:
    pymysql = import_module("pymysql")
    pymysql.version_info = (2, 2, 1, "final", 0)
    pymysql.__version__ = "2.2.1"
    pymysql.install_as_MySQLdb()


configure_mysql_driver()
import_module("dotenv").load_dotenv(BASE_DIR / ".env")


def env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "t", "yes", "y", "on"}


def env_list(name: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(name, default).split(",") if item.strip()]

_DEFAULT_INSECURE_SECRET = "dev-only-secret-key"
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY", _DEFAULT_INSECURE_SECRET)
DEBUG = env_bool("DJANGO_DEBUG", default=True)
ALLOWED_HOSTS = env_list("DJANGO_ALLOWED_HOSTS", default="127.0.0.1,localhost")
SECURE_SSL_REDIRECT = env_bool("SECURE_SSL_REDIRECT", default=not DEBUG)
SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "0"))
SECURE_HSTS_INCLUDE_SUBDOMAINS = env_bool("SECURE_HSTS_INCLUDE_SUBDOMAINS", default=not DEBUG)
SECURE_HSTS_PRELOAD = env_bool("SECURE_HSTS_PRELOAD", default=not DEBUG)
SESSION_COOKIE_SECURE = env_bool("SESSION_COOKIE_SECURE", default=not DEBUG)
CSRF_COOKIE_SECURE = env_bool("CSRF_COOKIE_SECURE", default=not DEBUG)

if not DEBUG and SECRET_KEY == _DEFAULT_INSECURE_SECRET:
    raise ImproperlyConfigured("DJANGO_SECRET_KEY must be configured in production.")

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "enterprise_documents",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "enterprise_documents.middleware.RequestIdMiddleware",
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
ASGI_APPLICATION = "config.asgi.application"

if os.getenv("MYSQL_DATABASE"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.mysql",
            "NAME": os.getenv("MYSQL_DATABASE", "facturasii"),
            "USER": os.getenv("MYSQL_USER", "root"),
            "PASSWORD": os.getenv("MYSQL_PASSWORD", ""),
            "HOST": os.getenv("MYSQL_HOST", "localhost"),
            "PORT": os.getenv("MYSQL_PORT", "3306"),
            "OPTIONS": {
                "charset": "utf8mb4",
            },
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "storage" / "app.db",
        }
    }

LANGUAGE_CODE = "es-cl"
TIME_ZONE = os.getenv("APP_TIME_ZONE", "America/Santiago")
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

STORAGE_ROOT = Path(os.getenv("STORAGE_PATH", BASE_DIR / "storage"))
STORAGE_ROOT.mkdir(parents=True, exist_ok=True)

DEFAULT_BRAND_NAME = os.getenv("DEFAULT_BRAND_NAME", "FacturaSII")
DEFAULT_BRAND_PRIMARY = os.getenv("DEFAULT_BRAND_PRIMARY", "#0F4C81")

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "enterprise_documents.authentication.JWTAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
    "DEFAULT_RENDERER_CLASSES": [
        "rest_framework.renderers.JSONRenderer",
    ],
    "DEFAULT_PARSER_CLASSES": [
        "rest_framework.parsers.JSONParser",
        "rest_framework.parsers.MultiPartParser",
        "rest_framework.parsers.FormParser",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ]
    if env_bool("ENABLE_DRF_THROTTLING", default=not DEBUG)
    else [],
    "DEFAULT_THROTTLE_RATES": {
        "anon": os.getenv("DRF_THROTTLE_ANON_RATE", "300/hour" if DEBUG else "60/hour"),
        "user": os.getenv("DRF_THROTTLE_USER_RATE", "2000/hour" if DEBUG else "300/hour"),
        "login": os.getenv("DRF_THROTTLE_LOGIN_RATE", "20/hour"),
        "document_import": os.getenv("DRF_THROTTLE_DOCUMENT_IMPORT_RATE", "120/hour"),
        "sii_sync": os.getenv("DRF_THROTTLE_SII_SYNC_RATE", "30/hour"),
    },
}

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://127.0.0.1:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", CELERY_BROKER_URL)
CELERY_TASK_ALWAYS_EAGER = os.getenv("CELERY_TASK_ALWAYS_EAGER", "false").lower() == "true"
CELERY_TASK_EAGER_PROPAGATES = os.getenv("CELERY_TASK_EAGER_PROPAGATES", "true").lower() == "true"
CELERY_TASK_IGNORE_RESULT = os.getenv("CELERY_TASK_IGNORE_RESULT", "true").lower() == "true"
CELERY_TASK_STORE_EAGER_RESULT = os.getenv("CELERY_TASK_STORE_EAGER_RESULT", "false").lower() == "true"
CELERY_FALLBACK_TO_SYNC_ON_ERROR = os.getenv("CELERY_FALLBACK_TO_SYNC_ON_ERROR", str(DEBUG).lower()).lower() == "true"
CELERY_BEAT_SCHEDULE = {
    "sync-enabled-sii-tenants": {
        "task": "enterprise_documents.tasks.sync_enabled_sii_profiles",
        "schedule": int(os.getenv("CELERY_SII_SYNC_INTERVAL_SECONDS", "300")),
    }
}

JWT_ACCESS_COOKIE_NAME = os.getenv("JWT_ACCESS_COOKIE_NAME", "facturasii_access")
JWT_REFRESH_COOKIE_NAME = os.getenv("JWT_REFRESH_COOKIE_NAME", "facturasii_refresh")
JWT_ACCESS_LIFETIME_SECONDS = int(os.getenv("JWT_ACCESS_LIFETIME_SECONDS", "900"))
JWT_REFRESH_LIFETIME_SECONDS = int(os.getenv("JWT_REFRESH_LIFETIME_SECONDS", "604800"))
JWT_COOKIE_SECURE = env_bool("JWT_COOKIE_SECURE", default=not DEBUG)
JWT_COOKIE_SAMESITE = os.getenv("JWT_COOKIE_SAMESITE", "Lax")

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "request_id": {
            "()": "enterprise_documents.logging_utils.RequestIdFilter",
        }
    },
    "formatters": {
        "json": {
            "()": "enterprise_documents.logging_utils.JsonFormatter",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "filters": ["request_id"],
            "formatter": "json",
        }
    },
    "root": {
        "handlers": ["console"],
        "level": os.getenv("LOG_LEVEL", "INFO"),
    },
}
