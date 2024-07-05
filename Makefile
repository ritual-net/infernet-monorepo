include scripts/setup.mk
include scripts/docs.mk
include scripts/gcp.mk
include scripts/pypi.mk
include infernet_services/services.mk

SHELL := /bin/bash

# suppress "entering directory" messages
MAKEFLAGS += --no-print-directory

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
ifdef changed
	$(eval ls_flag := --modified)
else
	$(eval ls_flag := )
endif
ifdef continue
	$(eval post := || true)
else
	$(eval post := )
endif
	@if [ -n "$(restart_env)" ]; then \
		uv venv -p 3.11 && \
		source .venv/bin/activate && \
		$(MAKE) generate-uv-env-file && source uv.env && \
		uv pip install -r infernet_services/requirements-precommit.lock; \
	fi
	$(MAKE) pre-commit -C infernet_services ls_flag=$(ls_flag) $(post)
	$(MAKE) prod-mode
	files=$$(git ls-files $(ls_flag) infernet_services) && \
	pre-commit run black --files $$files $(post) && \
	pre-commit run isort --files $$files $(post) && \
	pre-commit run ruff  --files $$files $(post) && \
	pre-commit run end-of-file-fixer --files $$files $(post) && \
	pre-commit run check-added-large-files --files $$files $(post) && \
	pre-commit run trailing-whitespace --files $$files $(post) && \
	pre-commit run mypy --files ./tools/*.py $(post)

test-library:
ifdef test_name
	$(eval test_name_cmd := -k $(test_name))
else
	$(eval test_name_cmd := )
endif
	PYTHONPATH=libraries/$(library)/src pytest libraries/$(library) $(test_name_cmd)
