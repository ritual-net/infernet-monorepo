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
