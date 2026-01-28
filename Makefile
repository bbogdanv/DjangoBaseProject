.PHONY: help build up down migrate test lint logs ps shell superuser clean

help:
	@echo "Available commands:"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start services"
	@echo "  make down       - Stop services"
	@echo "  make migrate    - Run migrations"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make logs       - Show logs"
	@echo "  make ps          - Show running containers"
	@echo "  make shell       - Django shell"
	@echo "  make superuser   - Create superuser"
	@echo "  make clean       - Clean up containers and volumes"

build:
	docker compose -f docker/docker-compose.yml --env-file .env build

up:
	docker compose -f docker/docker-compose.yml --env-file .env up -d

up-dev:
	docker compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml --env-file .env up -d

up-prod:
	docker compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml --env-file .env up -d

down:
	docker compose -f docker/docker-compose.yml --env-file .env down

down-volumes:
	docker compose -f docker/docker-compose.yml --env-file .env down -v

migrate:
	docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py migrate

makemigrations:
	docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py makemigrations

test:
	docker compose -f docker/docker-compose.yml --env-file .env exec backend pytest

lint:
	docker compose -f docker/docker-compose.yml --env-file .env exec backend ruff check .
	docker compose -f docker/docker-compose.yml --env-file .env exec backend black --check .

lint-fix:
	docker compose -f docker/docker-compose.yml --env-file .env exec backend ruff check --fix .
	docker compose -f docker/docker-compose.yml --env-file .env exec backend black .

logs:
	docker compose -f docker/docker-compose.yml --env-file .env logs -f

logs-backend:
	docker compose -f docker/docker-compose.yml --env-file .env logs -f backend

ps:
	docker compose -f docker/docker-compose.yml --env-file .env ps

shell:
	docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py shell

superuser:
	docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py createsuperuser

collectstatic:
	docker compose -f docker/docker-compose.yml --env-file .env exec backend python manage.py collectstatic --noinput

clean:
	docker compose -f docker/docker-compose.yml down -v
	docker system prune -f
