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

setup-library-env:
	uv venv -p 3.11 && \
	source .venv/bin/activate && \
	uv pip install -r libraries/$(library)/requirements.lock

pre-commit-library:
	@if [ -n "$(restart_env)" ]; then \
		$(MAKE) setup-library-env && \
		uv pip install -r pyproject.toml; \
	fi
	PYTHONPATH=libraries/$(library)/src pre-commit run \
		--files $$(git ls-files | grep -vE '^infernet_services/' | grep 'libraries/$(library)')

pre-commit-services:
	@if [ -n "$(restart_env)" ]; then \
		uv venv -p 3.11 && \
		source .venv/bin/activate && \
		uv pip install -r infernet_services/requirements-precommit.lock; \
	fi
	$(MAKE) pre-commit -C infernet_services
	pre-commit run ruff  --files $$(git ls-files infernet_services)
	pre-commit run black --files $$(git ls-files infernet_services)
	pre-commit run isort --files $$(git ls-files infernet_services)
	pre-commit run end-of-file-fixer --files $$(git ls-files infernet_services)
	pre-commit run check-added-large-files --files $$(git ls-files infernet_services)
	pre-commit run trailing-whitespace --files $$(git ls-files infernet_services)

test-library:
ifdef test_name
	$(eval test_name_cmd := -k $(test_name))
else
	$(eval test_name_cmd := )
endif
	PYTHONPATH=libraries/$(library)/src pytest libraries/$(library) $(test_name_cmd)
