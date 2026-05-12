# Raíz del repo (donde está este Makefile)
ROOT := $(shell cd "$(dir $(abspath $(lastword $(MAKEFILE_LIST))))" && pwd)
BACKEND_DIR := $(ROOT)/backend
FRONTEND_DIR := $(ROOT)/frontend

# Backend: app ASGI y servidor
UVICORN_APP ?= app.main:app
BACKEND_HOST ?= 0.0.0.0
BACKEND_PORT ?= 8000

# Frontend: script de npm (p. ej. dev, start)
FRONTEND_SCRIPT ?= dev

.DEFAULT_GOAL := help

.PHONY: help install install-backend install-frontend backend frontend dev clean-pyc

help: ## Muestra los comandos disponibles (helpers)
	@echo "Uso: make <objetivo>"
	@echo ""
	@grep -E '^[a-zA-Z0-9_.-]+:.*?## .*$$' "$(MAKEFILE_LIST)" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-22s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "Variables útiles:"
	@echo "  FRONTEND_SCRIPT=dev   script npm (make frontend FRONTEND_SCRIPT=start)"
	@echo "  BACKEND_PORT=8000     puerto del API"
	@echo "  FRONTEND_DIR=$(FRONTEND_DIR)"

install: install-backend install-frontend ## Instala dependencias de backend y frontend

install-backend: ## poetry install en backend/
	cd "$(BACKEND_DIR)" && poetry install

install-frontend: ## npm install en frontend/ (requiere package.json)
	@test -f "$(FRONTEND_DIR)/package.json" || (echo "No existe $(FRONTEND_DIR)/package.json. Crea el frontend o exporta FRONTEND_DIR=..." && exit 1)
	cd "$(FRONTEND_DIR)" && npm install

backend: ## Levanta la API FastAPI con Poetry + Uvicorn (cwd: backend/)
	cd "$(BACKEND_DIR)" && poetry run uvicorn "$(UVICORN_APP)" --host "$(BACKEND_HOST)" --port "$(BACKEND_PORT)" --reload

frontend: ## Levanta el frontend con npm run (script: FRONTEND_SCRIPT, por defecto dev)
	@test -f "$(FRONTEND_DIR)/package.json" || (echo "No existe $(FRONTEND_DIR)/package.json. Crea el frontend o exporta FRONTEND_DIR=..." && exit 1)
	cd "$(FRONTEND_DIR)" && npm run "$(FRONTEND_SCRIPT)"

dev: ## Levanta backend y frontend en paralelo (mismo make; Ctrl+C detiene ambos)
	@$(MAKE) -j2 backend frontend

clean-pyc: ## Elimina __pycache__ y .pyc bajo backend/
	find "$(BACKEND_DIR)" -type d -name __pycache__ -prune -exec rm -rf {} + 2>/dev/null || true
	find "$(BACKEND_DIR)" -type f -name '*.py[co]' -delete 2>/dev/null || true
