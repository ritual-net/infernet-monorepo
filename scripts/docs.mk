# Make commands for building docs website for our python projects.

# if the .venv directory exists, use the python binary from there
# otherwise use the system python

SHELL := /bin/bash
PYTHON := $(if $(wildcard ./.venv/),./.venv/bin/python,python)

generate-library-docs:
	@eval "$$get_library"; \
	$(PYTHON) tools/generate_docs.py $$library

generate-services-docs:
	PYTHONPATH=tools $(PYTHON) tools/generate_services_docs.py

serve-library-docs:
	@eval "$$get_library"; \
	$(MAKE) clean-library-docs generate-library-docs build-library-docs library=$$library; \
	cd libraries/$$library && PYTHONPATH=src mkdocs serve

serve-services-docs:
	cd infernet_services && mkdocs serve

build-library-docs:
	@eval "$$get_library"; \
	cd libraries/$$library && PYTHONPATH=src mkdocs build

build-services-docs:
	cd infernet_services && PYTHONPATH=src mkdocs build

clean-library-docs:
	@eval "$$get_library"; \
	rm -rf libraries/$$library/site; \
	rm -rf libraries/$$library/docs/reference

clean-services-docs:
	rm -rf infernet_services/site
	rm -rf infernet_services/docs/reference

prod :=

deploy-library-docs: clean-library-docs
	@eval "$$get_library"; \
	rm -rf .vercel || true; \
	$(MAKE) generate-library-docs build-library-docs library=$$library; \
	$(PYTHON) tools/deploy_docs.py $$library $(prod)

deploy-services-docs: clean-services-docs
	rm -rf .vercel || true
	$(MAKE) generate-services-docs build-services-docs
	$(PYTHON) tools/deploy_docs.py infernet_services $(prod)

sync-readme:
	rsync infernet_services/services/$(service)/README.md \
		infernet_services/docs/reference/$(service).md

watch:
	fswatch -0 "infernet_services/services/$(service)/README.md" | while read -d "" event ; \
	do \
	    $(MAKE) sync-readme; \
	done
