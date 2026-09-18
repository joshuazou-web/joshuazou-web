.PHONY: install test demo snapshot api web verify lint all

install:
	pip install -e '.[dev]'

test:
	python -m pytest

demo:
	python -m corridoros.cli demo

snapshot:
	python -m corridoros.cli snapshot data/snapshot.json

verify:
	python -m corridoros.cli verify-audit
	python -m corridoros.cli boundary

api:
	pip install -e '.[api]' && uvicorn apps.api.main:app --reload

web:
	cd apps/web && npm install && npm run dev

lint:
	ruff check src apps tests

all: test snapshot verify
