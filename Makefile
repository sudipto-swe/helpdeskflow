.PHONY: help install lint type-check test test-cov run demo clean docker-up docker-down

VENV := .venv
PYTHON := $(VENV)/bin/python
PIP := $(VENV)/bin/pip
UVICORN := $(VENV)/bin/uvicorn
PYTEST := $(VENV)/bin/pytest
RUFF := $(VENV)/bin/ruff
MYPY := $(VENV)/bin/mypy

help:
	@echo "HelpdeskFlow Makefile commands:"
	@echo "  make install     - Install python & node dependencies"
	@echo "  make lint        - Run ruff linter & format checks"
	@echo "  make type-check  - Run mypy static type checking"
	@echo "  make test        - Run unit and integration tests"
	@echo "  make test-cov    - Run pytest with coverage report"
	@echo "  make synth       - Generate synthetic datasets"
	@echo "  make seed        - Ingest KB & seed database"
	@echo "  make run         - Run FastAPI backend locally"
	@echo "  make demo        - Execute full end-to-end ticket triage demo"
	@echo "  make eval        - Run golden set and adversarial evaluations"

install:
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt

lint:
	$(RUFF) check .

type-check:
	$(MYPY) apps/api/app

test:
	$(PYTEST) apps/api/tests -v

test-cov:
	$(PYTEST) apps/api/tests --cov=apps/api/app --cov-report=term-missing

synth:
	$(PYTHON) synth/generate_kb.py
	$(PYTHON) synth/generate_customers.py
	$(PYTHON) synth/generate_tickets.py

seed:
	$(PYTHON) scripts/seed.py

run:
	$(UVICORN) apps.api.app.main:app --host 0.0.0.0 --port 8000 --reload

demo:
	$(PYTHON) scripts/demo.py

eval:
	$(PYTHON) eval/run_eval.py --provider mock

clean:
	rm -rf .pytest_cache .mypy_cache .ruff_cache __pycache__ apps/api/app/__pycache__
	find . -type d -name "__pycache__" -exec rm -rf {} +
