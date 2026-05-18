.PHONY: install run test test-cov lint format migrate db-start db-stop db-reset

install:
	poetry install

run:
	poetry run uvicorn app.main:app --reload --port 8000

test:
	poetry run pytest tests/ -v

test-cov:
	poetry run pytest tests/ --cov=app --cov-report=term-missing

lint:
	poetry run black --check app tests
	poetry run mypy app tests

format:
	poetry run black app tests

migrate:
	poetry run alembic upgrade head

db-start:
	docker-compose -f ../docker-compose.yml up -d db

db-stop:
	docker-compose -f ../docker-compose.yml stop db

db-reset:
	docker-compose -f ../docker-compose.yml down -v db
	docker-compose -f ../docker-compose.yml up -d db
	@echo "Waiting for DB to start..."
	sleep 3
	poetry run alembic upgrade head
