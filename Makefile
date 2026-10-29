PYTHON ?= python3.12
VENV ?= .venv
PY := $(VENV)/bin/python

.PHONY: setup test verify build smoke run
setup:
	$(PYTHON) -m venv $(VENV)
	$(PY) -m pip install -r requirements-build.txt
	$(PY) -m pip install --no-build-isolation --no-deps .

test:
	$(PY) -m unittest discover -s tests
	node --test tests/*.mjs

verify:
	$(PY) scripts/verify_evidence.py

build: verify
	$(PY) -m build --no-isolation

smoke:
	$(PY) scripts/smoke_wheel.py

run:
	$(VENV)/bin/resolve-demo
