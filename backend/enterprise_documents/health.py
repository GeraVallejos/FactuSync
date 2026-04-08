from __future__ import annotations

from pathlib import Path

from django.conf import settings
from django.db import connection


def health_snapshot() -> dict:
    db_ok = _check_database()
    storage_ok = _check_storage(settings.STORAGE_ROOT)
    celery_ok = bool(settings.CELERY_BROKER_URL)

    checks = {
        "database": "ok" if db_ok else "error",
        "storage": "ok" if storage_ok else "error",
        "celery": "ok" if celery_ok else "error",
    }
    status = "ok" if all(value == "ok" for value in checks.values()) else "degraded"
    return {
        "status": status,
        "checks": checks,
        "celery_eager": bool(settings.CELERY_TASK_ALWAYS_EAGER),
    }


def _check_database() -> bool:
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
        return True
    except Exception:
        return False


def _check_storage(storage_root: Path) -> bool:
    try:
        storage_root.mkdir(parents=True, exist_ok=True)
        return storage_root.exists() and storage_root.is_dir()
    except Exception:
        return False
