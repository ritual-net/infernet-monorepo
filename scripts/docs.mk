# Make commands for building docs website for our python projects.

# if the .venv directory exists, use the python binary from there
# otherwise use the system python
SHELL := /bin/bash
PYTHON := $(if $(wildcard ./.venv/),./.venv/bin/python,python)

generate-library-docs:
	$(PYTHON) tools/generate_docs.py $(library)

generate-services-docs:
	PYTHONPATH=tools $(PYTHON) tools/generate_services_docs.py

serve-library-docs:
	cd libraries/$(library) && PYTHONPATH=src mkdocs serve

serve-services-docs:
	cd infernet_services && mkdocs serve

build-library-docs:
	cd libraries/$(library) && PYTHONPATH=src mkdocs build

build-services-docs:
	cd infernet_services && PYTHONPATH=src mkdocs build

clean-library-docs:
	rm -rf libraries/$(library)/site
	rm -rf libraries/$(library)/docs/reference

clean-services-docs:
	rm -rf infernet_services/site
	rm -rf infernet_services/docs/reference

deploy-library-docs: clean-library-docs
	rm -rf .vercel || true
	$(MAKE) generate-library-docs build-library-docs
	$(PYTHON) tools/deploy_docs.py $(library)

deploy-services-docs: clean-services-docs
	rm -rf .vercel || true
	$(MAKE) generate-services-docs build-services-docs
	$(PYTHON) tools/deploy_docs.py infernet_services
