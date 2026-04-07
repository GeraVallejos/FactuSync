# Factura SII Backend

Backend enterprise basado en Django + Django REST Framework para:

- Ingestar XML DTE desde multiples fuentes.
- Normalizar el XML a un modelo interno desacoplado del SII.
- Validar reglas tributarias base.
- Guardar XML original, PDF generado y trazabilidad completa.
- Exponer API multi-tenant lista para integrarse con tu ERP.
- Procesar ingestion y sincronizacion con Celery + Redis.

## Stack

- Django 5
- Django REST Framework
- Celery
- Redis
- MySQL como base principal
- PyMySQL como driver

## Arquitectura

- `enterprise_documents/dte`: parser, modelos y validaciones tributarias.
- `enterprise_documents/storage.py` y `enterprise_documents/pdf_renderer.py`: storage XML/PDF y renderer base.
- `enterprise_documents`: modelos Django, servicios, API REST, admin y tareas Celery.
- `config`: settings, urls y entrypoints WSGI/ASGI.

## Variables de entorno MySQL

El proyecto carga `backend/.env` automaticamente.

Configuracion creada por defecto:

```env
MYSQL_DATABASE=facturasii
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_HOST=localhost
MYSQL_PORT=3306
```

Si tu MySQL usa password, solo actualiza `MYSQL_PASSWORD` en `backend/.env`.

## Variables Celery / Redis

```env
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
CELERY_TASK_ALWAYS_EAGER=false
CELERY_TASK_EAGER_PROPAGATES=true
CELERY_SII_SYNC_INTERVAL_SECONDS=300
```

## Puesta en marcha

```powershell
cd backend
venv\Scripts\python -m pip install -e .
venv\Scripts\python manage.py migrate
venv\Scripts\python manage.py runserver
```

En otra terminal:

```powershell
cd backend
venv\Scripts\celery -A config worker -l info
```

Para sync programado SII:

```powershell
cd backend
venv\Scripts\celery -A config beat -l info
```

## Endpoints

- `GET /api/health`
- `POST /api/documentos/importar`
- `GET /api/documentos`
- `GET /api/documentos/{id}`
- `GET /api/documentos/{id}/pdf`
- `GET /api/documentos/{id}/xml`
- `GET /api/documentos/{id}/audit`
- `POST /api/documentos/{id}/reprocesar`
- `GET /api/dashboard`
- `POST /api/sii/test-auth`
- `POST /api/sii/sync`

En modo standalone, puedes autenticarte con JWT HttpOnly y operar sin headers de tenant.
Tambien puedes enviar contexto desde ERP con `X-ERP-Tenant-Id` y `X-ERP-Company-Id`.

## Perfil SII real

Para probar autenticacion real contra SII:

1. Configura tu empresa y perfil SII desde `POST/PATCH /api/me/tax-profile`.
2. Guarda `certificate_path` apuntando a tu `.pfx` o `.p12`.
3. Envia `certificate_password` solo cuando quieras definir o actualizar la clave.
4. Usa `POST /api/sii/test-auth` para validar `CrSeed -> firma -> GetTokenFromSeed`.

El backend usa los endpoints oficiales documentados por SII:
- certificacion: `maullin.sii.cl`
- produccion: `palena.sii.cl`

## Ejemplo de importacion

```powershell
curl -X POST http://127.0.0.1:8000/api/documentos/importar `
  -H "X-Tenant-Id: demo" `
  -H "X-Actor: admin@demo" `
  -F "file=@C:\ruta\documento.xml"
```

## Siguiente iteracion recomendada

1. Conectar autenticacion y permisos por usuario/empresa.
2. Mover el procesamiento a Celery con Redis o RabbitMQ.
3. Integrar SII como fuente real de ingestión.
4. Mejorar el renderer PDF con plantillas HTML corporativas.
5. Conectar eventos al ERP multi-tenant.
