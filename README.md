# PulseNotify

Flight price monitoring backend built with **Django**, **Django REST Framework**, **Celery**, **Redis**, and **PostgreSQL**.

Users create price alerts for routes (e.g. `DEL-BOM`). Celery Beat checks prices every 60 seconds against an internal mock feed. When a price drops to or below the threshold, `send_notification` runs asynchronously and writes a `NotificationLog`.

## Prerequisites

- Python 3.11+ (tested with 3.13)
- Docker Desktop (PostgreSQL + Redis)
- Postman (optional — import the included collection)

## Quick start

### 1. Virtualenv and dependencies

```bash
cd "Pulse Notify"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment

```bash
cp .env.example .env
```

Defaults match `docker-compose.yml`.  
`DJANGO_SETTINGS_MODULE` should be `pulsenotify.settings.local` for development.

### 3. Start PostgreSQL and Redis

```bash
docker compose up -d
```

### 4. Migrate

```bash
python manage.py migrate
```

### 5. Run all three processes

You need **three terminals** (venv activated in each):

**Terminal 1 — Django API**

```bash
python manage.py runserver
```

**Terminal 2 — Celery worker**

```bash
celery -A pulsenotify worker --loglevel=info
```

**Terminal 3 — Celery Beat**

```bash
celery -A pulsenotify beat --loglevel=info
```

- Terminal 3: `check_prices` every 60 seconds  
- Terminal 2: `send_notification` when a threshold is hit  

## API overview

| Method | Path | Auth |
|--------|------|------|
| POST | `/api/auth/register/` | Public |
| POST | `/api/auth/login/` | Public |
| POST | `/api/alerts/` | JWT |
| GET | `/api/alerts/` | JWT |
| DELETE | `/api/alerts/<id>/` | JWT (soft-deactivate → `inactive`) |
| GET | `/api/flights/price/?route=DEL-BOM` | Public |
| GET | `/api/admin/summary/` | JWT + admin role |

### Register

```bash
curl -X POST http://localhost:8000/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"securepass","email":"alice@example.com"}'
```

### Create alert

```bash
curl -X POST http://localhost:8000/api/alerts/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{"origin":"DEL","destination":"BOM","threshold_price":"4500.00"}'
```

## Promote a user to admin

```bash
python manage.py shell
```

```python
from django.contrib.auth.models import User
from pulse.models import UserProfile

u = User.objects.get(username='alice')
u.profile.role = UserProfile.Role.ADMIN
u.profile.save()
```

Log in again (or reuse a token — role is checked live on the profile), then call `GET /api/admin/summary/`.

For Postman request **13**, set collection variable `admin_access_token` to that user’s JWT.

## Tests

```bash
python manage.py test
```

## Postman

Import [`PulseNotify.postman_collection.json`](PulseNotify.postman_collection.json) — 13 scenarios covering register/login, alerts, price feed, and admin access.

## Project layout

```
pulsenotify/          # Django project
  settings/
    base.py           # shared (DRF, JWT, Celery Beat)
    local.py          # DEBUG=True, local Postgres
    production.py     # DEBUG=False
  celery.py
pulse/                # main app
  models.py
  views.py
  tasks.py
  signals.py
  permissions.py
  tests.py
docker-compose.yml    # Postgres 16 + Redis 7
```

## Settings environments

| Module | Use |
|--------|-----|
| `pulsenotify.settings.local` | Local development |
| `pulsenotify.settings.production` | Production (`DEBUG=False`) |
