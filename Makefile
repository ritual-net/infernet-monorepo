include scripts/setup.mk
include scripts/utils.mk
include scripts/docs.mk
include scripts/gcp.mk
include scripts/pypi.mk
include scripts/libraries.mk
include scripts/rust_bindings.mk
include infernet_services/services.mk


update-lockfile:
	@requirements_path=`find . -maxdepth 4 | grep "requirements*.txt" | fzf`; \
	requirements_path=`echo $$requirements_path | xargs realpath`; \
	rm -rf temp_lock; \
	mkdir -p temp_lock; \
	cp $$requirements_path temp_lock/; \
	lockfile_path=`echo $$requirements_path | sed 's/.txt/.lock/'`; \
	index_url=`make get-index-url`; \
	cd temp_lock; \
	uv venv -p 3.11 && source .venv/bin/activate; \
	uv pip install -r $$requirements_path --extra-index-url $$index_url; \
	uv pip freeze | grep -v "file://" > "$$lockfile_path"; \
	rm -rf ../temp_lock; \
	echo "✅ Updated lockfile at $$lockfile_path"

SHELL := /bin/bash

# suppress "entering directory" messages
MAKEFLAGS += --no-print-directory

clean:
	rm -rf dist

setup-library-env:
	@eval "$$get_library"; \
	if [ -z "$$library" ]; then \
		echo "No library selected, please select one"; \
		exit 1; \
	fi; \
	uv venv -p 3.11 && \
	source .venv/bin/activate && \
	uv pip install -r pyproject.toml && \
	uv pip install -r libraries/$$library/requirements.lock

pre-commit-library:
	@eval "$$get_library"; \
	if [ -n "$(restart_env)" ]; then \
		$(MAKE) setup-library-env && \
		uv pip install -r pyproject.toml; \
	fi; \
	export PYTHONPATH=infernet_services/tests:libraries/$$library/src && \
	source .venv/bin/activate && \
	pre-commit run --files `git ls-files | grep -vE '^infernet_services/' | grep -E "(libraries/$$library|infernet_services/tests/test_library)"`

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
	@eval "$$get_library"; \
	PYTHONPATH=.:./tools:./infernet_services/tests:./libraries/$$library/src pytest libraries/$$library $(test_name_cmd)
