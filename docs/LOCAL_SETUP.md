# LOCAL_SETUP.md
# Local Development Setup — From Zero to Running

---

## Prerequisites

Install these before anything else:

- Python 3.11 — https://python.org
- Poetry — https://python-poetry.org/docs/#installation
- Docker Desktop — https://www.docker.com/products/docker-desktop
- Git

Verify installs:
```bash
python3.11 --version    # must show Python 3.11.x
poetry --version         # must show Poetry 1.x or 2.x
docker --version         # must show Docker version
```

---

## Step 1 — Clone and Configure Python Version

```bash
git clone <repo-url>
cd passive-wealth-engine
```

Verify the correct Python version is active:
```bash
cat .python-version      # should show 3.11
python --version         # should show Python 3.11.x
```

If Poetry is not using 3.11:
```bash
poetry env use python3.11
```

---

## Step 2 — Install Dependencies

```bash
cd backend
poetry install
```

This installs all dependencies from `poetry.lock`. Every developer gets identical package versions.

---

## Step 3 — Configure Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in these values:

```env
DATABASE_URL=postgresql+asyncpg://pwre_user:pwre_pass@localhost:5432/pwre_db
ENVIRONMENT=development
LOG_LEVEL=INFO
NSE_REQUEST_TIMEOUT=30
YAHOO_FINANCE_TIMEOUT=30
```

All values in `.env.example` with empty values are required. The application will fail at startup with a clear error message if any are missing.

---

## Step 4 — Start PostgreSQL via Docker

```bash
docker-compose up -d db
```

Verify it is running:
```bash
docker-compose ps
```

You should see the `db` service with status `Up`.

---

## Step 5 — Run Database Migrations

```bash
poetry run alembic upgrade head
```

This creates all tables in PostgreSQL. Run this every time a new migration is added.

If you see an error about the database not existing:
```bash
docker exec -it pwre-db psql -U postgres -c "CREATE DATABASE pwre_db;"
docker exec -it pwre-db psql -U postgres -c "CREATE USER pwre_user WITH PASSWORD 'pwre_pass';"
docker exec -it pwre-db psql -U postgres -c "GRANT ALL PRIVILEGES ON DATABASE pwre_db TO pwre_user;"
```

Then re-run `alembic upgrade head`.

---

## Step 6 — Start the Application

```bash
poetry run uvicorn app.main:app --reload --port 8000
```

The `--reload` flag restarts the server automatically on code changes.

You should see:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process
```

---

## Step 7 — Verify Everything Works

Open the interactive API docs:
```
http://localhost:8000/docs
```

You should see the full API with all endpoints listed and testable.

Try the health check endpoint:
```bash
curl http://localhost:8000/health
```

Expected response:
```json
{"status": "ok", "database": "connected"}
```

---

## Step 8 — Run the Test Suite

```bash
make test
```

Or without Make:
```bash
poetry run pytest tests/ -v
```

All tests should pass on a fresh setup. If any fail, check the error output carefully — it will tell you exactly which assertion failed.

---

## Makefile Commands Reference

```bash
make install      # poetry install
make run          # start uvicorn with reload
make test         # run full test suite
make test-cov     # run tests with coverage report
make lint         # run black check + mypy
make format       # run black to auto-format code
make migrate      # alembic upgrade head
make db-start     # docker-compose up -d db
make db-stop      # docker-compose stop db
make db-reset     # drop and recreate database, re-run migrations
```

---

## Stopping Everything

```bash
# Stop the FastAPI server
CTRL+C in the terminal running uvicorn

# Stop PostgreSQL
docker-compose stop db

# Stop and remove containers + volumes (clean slate)
docker-compose down -v
```

---

## Common Problems

**Problem:** `poetry install` fails with Python version error
**Fix:** Run `poetry env use python3.11` first

**Problem:** Alembic migration fails with connection refused
**Fix:** Make sure Docker is running and `docker-compose up -d db` completed successfully

**Problem:** NSE data fetch returns 401 or empty
**Fix:** Normal behaviour if NSE session cookie has expired. The ingestion module handles re-establishing the session automatically. If it persists, check your internet connection.

**Problem:** `make` command not found on Windows
**Fix:** Install Make via Chocolatey (`choco install make`) or run the Poetry commands directly as listed above
