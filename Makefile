include scripts/setup.mk
include scripts/utils.mk
include scripts/docs.mk
include scripts/gcp.mk
include scripts/pypi.mk
include scripts/libraries.mk
include scripts/rust_bindings.mk
include infernet_services/services.mk


update-lockfile:
	@requirements_path=`find . -maxdepth 4 | grep "requirements.*.txt" | fzf`; \
	if [ -z "$$requirements_path" ]; then \
		echo "No requirements file selected"; \
		exit 1; \
	fi; \
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
	cd libraries/$$library; \
	if [ -n "$(restart_env)" ] || [ ! -d .venv ]; then uv venv -p 3.11; fi; \
	source .venv/bin/activate && \
	uv pip install -r requirements.lock; \
	cd ../../ && \
	export PYTHONPATH=libraries/$$library/src:./infernet_services/tests && \
	pre-commit run --files `git ls-files | grep libraries/$$library`

define get_service
if [ -z "$(service)" ]; then \
	service=`ls infernet_services/services | grep -v pycache | fzf`; \
else \
	service=`ls infernet_services/services | grep -v pycache | grep $(service)`; \
fi;
endef

export get_service
pre-commit-service:
	eval "$$get_service"; \
	cd infernet_services/services/$$service; \
	if [ -n "$(restart_env)" ] || [ ! -d .venv ]; then uv venv -p 3.11; fi; \
	source .venv/bin/activate && \
	uv pip install -r requirements.txt; \
	uv pip install mypy isort; \
	pre-commit run --files `git ls-files`

test-library:
ifdef test_name
	$(eval test_name_cmd := -k $(test_name))
else
	$(eval test_name_cmd := )
endif
	@eval "$$get_library"; \
	PYTHONPATH=.:./tools:./infernet_services/tests:./libraries/$$library/src pytest libraries/$$library $(test_name_cmd)
