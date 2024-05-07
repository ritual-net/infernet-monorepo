# Make commands for building docs website for our python projects.

# if the .venv directory exists, use the python binary from there
# otherwise use the system python
SHELL := /bin/bash
PYTHON := $(if $(wildcard ./.venv/),./.venv/bin/python,python)

generate-docs:
	$(PYTHON) tools/generate_docs.py $(project)

serve-docs:
	cd projects/$(project) && PYTHONPATH=src mkdocs serve

build-docs:
	cd projects/$(project) && mkdocs build

build-docs-index:
	$(PYTHON) tools/build_docs_index.py

deploy-docs:
	vercel --prod
  