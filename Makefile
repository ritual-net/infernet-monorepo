include infernet_services/Services.mk
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

services-pre-commit:
	$(MAKE) -C ./infernet_services pre-commit

test:
	PYTHONPATH=projects/$(project)/src pytest projects/$(project)
