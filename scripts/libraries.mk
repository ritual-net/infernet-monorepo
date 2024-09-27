lib_path := libraries/$(lib_name)

define lib_pyproject
[project]
name = "$(lib_name)"
version = "0.1.0.0"
requires-python = ">=3.8"
classifiers = [
    "Programming Language :: Rust",
    "Programming Language :: Python :: Implementation :: CPython",
    "Programming Language :: Python :: Implementation :: PyPy",
]

[build-system]

requires = ["hatchling"]
build-backend = "hatchling.build"

[project.optional-dependencies]
development = [
]

[tool.rye]
managed = true
dev-dependencies = []

[tool.hatch.metadata]
allow-direct-references = true

[tool.hatch.build.targets.wheel]
packages = ["src/$(lib_name)"]
endef
export lib_pyproject

define starter_program
if __name__ == "__main__":
	print("Hello, World!")
endef
export starter_program

new-library:
	@if [ -f $(lib_path) ]; then \
		echo "⚠️ Library $(lib_name) already exists"; \
		exit 1; \
	else \
		mkdir -p $(lib_path)/src/$(lib_name); \
	fi
	@echo "$$lib_pyproject" > $(lib_path)/pyproject.toml
	@echo "$$starter_program" > $(lib_path)/src/$(lib_name)/hello.py
	@touch $(lib_path)/src/$(lib_name)/__init__.py
	@make update-library-lockfile library=$(lib_name)
	@echo "✅ Created new library $(lib_name)"

setup-library-env:
	@eval "$$get_library"; \
	if [ -z "$$library" ]; then \
		echo "No library selected, please select one"; \
		exit 1; \
	fi; \
	$(MAKE) generate-uv-env-file && source uv.env && \
	uv venv -p 3.11 && \
	source .venv/bin/activate && \
	uv pip install -r pyproject.toml && \
	uv pip install -r libraries/$$library/requirements.lock;

# updates the python lockfile of the specific library
update-library-lockfile:
	@eval "$$get_library"; \
	echo "Updating lockfile for $$library"; \
	$(MAKE) generate-uv-env-file && source uv.env && \
	optional_deps=`sed -n '/project.optional-dependencies/,/^\[/p' libraries/$$library/pyproject.toml | grep '^[a-zA-Z]' | awk '{print $$1}'`; \
	rm -rf temp_lock; \
	mkdir -p temp_lock; \
	cd temp_lock && uv venv -p 3.11 && source .venv/bin/activate && cd ..; \
	cd libraries/$$library; \
	for dep in $$optional_deps; do \
		echo "Installing $$dep"; \
		uv pip install -e ".[$$dep]"; \
	done; \
	uv pip freeze | grep -v "file://" > requirements.lock; \
	rm -rf temp_lock; \
	echo "✅ Updated lockfile for $$library"

pre-commit-library:
	@eval "$$get_library"; \
	cd libraries/$$library; \
	if [ -n "$(restart_env)" ] || [ ! -d .venv ]; then uv venv -p 3.11; fi; \
	source .venv/bin/activate && \
	$(MAKE) generate-uv-env-file && source uv.env && \
	uv pip install -r requirements.lock; \
	cd ../../ && \
	export PYTHONPATH=libraries/$$library/src:./infernet_services/tests && \
	pre-commit run --files `git ls-files | grep libraries/$$library`

test-library:
ifdef test_name
	$(eval test_name_cmd := -k $(test_name))
else
	$(eval test_name_cmd := )
endif
	@eval "$$get_library"; \
	source .env; \
	PYTHONPATH=.:./tools:./infernet_services/tests:./libraries/$$library/src pytest libraries/$$library $(test_name_cmd)
