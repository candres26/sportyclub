.PHONY: help up down backend-install migrate seed api admin test lint

help:
	@echo "SportyClub - comandos disponibles:"
	@echo "  make up              Levanta PostgreSQL con docker compose"
	@echo "  make down            Detiene los contenedores"
	@echo "  make backend-install Crea el venv e instala dependencias del backend"
	@echo "  make migrate         Aplica migraciones (crea rol app_user y RLS)"
	@echo "  make seed            Catalogo de permisos + superadmin de plataforma"
	@echo "  make api             Arranca la API con recarga en caliente"
	@echo "  make admin           Arranca el panel Next.js"
	@echo "  make test            Ejecuta la suite del backend"
	@echo "  make lint            Ruff + mypy del backend"

up:
	docker compose up -d postgres

down:
	docker compose down

backend-install:
	cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -e ".[dev]"

migrate:
	cd backend && . .venv/bin/activate && alembic upgrade head

seed:
	cd backend && . .venv/bin/activate && python -m scripts.seed

api:
	cd backend && . .venv/bin/activate && uvicorn app.main:app --reload

admin:
	cd admin && npm run dev

test:
	cd backend && . .venv/bin/activate && pytest -q

lint:
	cd backend && . .venv/bin/activate && ruff check app tests scripts && mypy app
