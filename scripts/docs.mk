# Make commands for building docs website for our python projects.

# if the .venv directory exists, use the python binary from there
# otherwise use the system python
SHELL := /bin/bash
PYTHON := $(if $(wildcard ./.venv/),./.venv/bin/python,python)

generate-docs:
	$(PYTHON) tools/generate_docs.py $(library)

generate-services-docs:
	PYTHONPATH=tools $(PYTHON) tools/generate_services_docs.py

serve-docs:
	cd libraries/$(library) && PYTHONPATH=src mkdocs serve

serve-services-docs:
	cd infernet_services && mkdocs serve

build-docs:
	cd libraries/$(library) && PYTHONPATH=src mkdocs build

build-services-docs:
	cd infernet_services && PYTHONPATH=src mkdocs build

clean-docs:
	rm -rf libraries/$(library)/site
	rm -rf libraries/$(library)/docs/reference

deploy-docs: clean-docs
	rm -rf .vercel || true
	$(MAKE) generate-docs build-docs
	$(PYTHON) tools/deploy_docs.py $(library)
