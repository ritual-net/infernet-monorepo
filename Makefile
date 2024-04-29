include infernet_services/services.mk
include scripts/docs.mk
include scripts/gcp.mk
include scripts/pypi.mk

ifneq ("$(wildcard gcp.env)","")
include gcp.env
endif

SHELL := /bin/bash

clean:
	rm -rf dist

pre-commit:
	pre-commit run --files $$(git ls-files projects/$(project))

pre-commit-services:
	$(MAKE) pre-commit -C infernet_services
	pre-commit run ruff  --files $$(git ls-files infernet_services)
	pre-commit run black --files $$(git ls-files infernet_services)
	pre-commit run isort --files $$(git ls-files infernet_services)
	pre-commit run end-of-file-fixer --files $$(git ls-files infernet_services)
	pre-commit run check-added-large-files --files $$(git ls-files infernet_services)
	pre-commit run trailing-whitespace --files $$(git ls-files infernet_services)

test:
	PYTHONPATH=projects/$(project)/src pytest projects/$(project)
