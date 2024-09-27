# Make commands for building python packages & publishing them to GCP's Artifact Registry
SHELL := /bin/bash

# Gets GCP's index URL for the artifact repository if a gcp.env file is present
ifneq ("$(wildcard gcp.env)","")
include gcp.env
$(eval token := $(shell gcloud auth print-access-token))
$(eval index_url := "https://_token:$(token)@$(artifact_location)-python.pkg.dev/$(gcp_project)/$(artifact_repo)/simple")
endif

# Conditional assignment based on the operating system
ifeq ($(shell uname -s),Darwin)
    SED := gsed
else
    SED := sed
endif

# setting the python library version.
# modifies the pyproject.toml file for the library at libraries/$(library)
set-version:
	$(SED) -i 's/version = .*/version = "$(version)"/' libraries/$(library)/pyproject.toml

build-library:
	@eval "$$get_library"; \
	rm `find dist | grep $(library)` || true; \
	rye build --pyproject libraries/$(library)/pyproject.toml

build-pyo3-library:
	if ! command -v maturin; then \
		uv pip install maturin; \
	fi; \
	rm `find dist | grep $(library)` || true; \
	make -C libraries/$(library) build

repository_url := https://$(artifact_location)-python.pkg.dev/$(gcp_project)/$(artifact_repo)/

# twine oauth2 username
username := _token

show-token:
	@echo $(token)

# explicit install command to test uv installation
uv-install:
	uv venv -p 3.11; \
	source .venv/bin/activate; \
	uv pip install --index-url https://pypi.org/simple --extra-index-url $(index_url) $(library)

# explicit install command to test pip installation
pip-install:
	pip install --index-url https://pypi.org/simple --extra-index-url $(index_url) $(library)

define get_library
if [ -z "$(library)" ]; then \
	library=`ls libraries | grep -v pycache | fzf`; \
else \
	library=`ls libraries | grep -v pycache | grep $(library) | head -n 1`; \
fi;
endef
export get_library

bump-lib-version:
	@eval "$$get_library"; \
	current_version=`grep "version = " libraries/$$library/pyproject.toml | awk '{print $$3}' | tr -d '"'`; \
	incremented=`python -c "cv='$$current_version'.split('.'); cv[-1]=str(int(cv[-1])+1); print('.'.join(cv))"`; \
	$(SED) -i "s/version = .*/version = \"$$incremented\"/" libraries/$$library/pyproject.toml; \
	echo "Bumped version from $$current_version to $$incremented";

publish-library:
	@eval "$$get_library"; \
	if [ -z "$(skip_bump)" ]; then \
		make bump-lib-version library=$$library; \
	fi; \
	is_pyo3=`grep "pyo3" libraries/$$library/pyproject.toml`; \
	if [ -z "$$is_pyo3" ]; then \
		make clean build-library library=$$library; \
	else \
		make clean build-pyo3-library library=$$library; \
	fi; \
	echo "getting access token"; \
	token=`make get-access-token`; \
	echo "publishing"; \
	rye publish --repository ritual-pypi \
		--repository-url $(repository_url) \
		--username $(username) \
		--token $$token \
		--yes \
		--verbose \
	 	dist/*

print-install-command:
	@echo "uv pip install --index-url https://pypi.org/simple --extra-index-url `make get-index-url` ritual-arweave==0.1.0"

publish-pypi:
	$(MAKE) clean build-library
	twine upload dist/*

# show the pypi registry settings (useful for modifying the ~/.pypirc file)
show-artifact-settings:
	gcloud artifacts print-settings python \
	    --project=$(gcp_project) \
	    --repository=$(artifact_repo) \
	    --location=$(artifact_location)

gcp-setup: activate-service-account get_index_url
	@echo "\n\nService account loaded 🎉."
	@echo "For uv setup add the following line to your .bashrc or .zshrc file:"
	@echo "\nexport UV_EXTRA_INDEX_URL=$(index_url)\n"
	@echo "Or simply set that env var everytime you're installing from uv."

export_prefix ?= "export "

get-access-token:
	@current_account=`gcloud config get account`; \
	gcloud auth activate-service-account --key-file=pypi-deployer-key.json > /dev/null 2>&1; \
	if [ -z "$(gcp_project)" ] || [ -z "$(artifact_location)" ] || [ -z "$(artifact_repo)" ]; then \
		echo "Please set the gcp_project, artifact_location & artifact_repo variables in the gcp.env file"; \
		exit 1; \
	fi; \
	gcloud auth print-access-token; \
	gcloud config set account $$current_account > /dev/null 2>&1 || true

get-index-url:
	@echo "https://_token:`make get-access-token`@$(artifact_location)-python.pkg.dev/$(gcp_project)/$(artifact_repo)/simple";

generate-uv-env-file:
	index_url=`make get-index-url`; \
	echo "$(export_prefix)UV_EXTRA_INDEX_URL=$$index_url" > uv.env

show-pip-command:
	@echo "uv pip install --extra-index-url `make get-index-url` $(library)"

ifeq ($(findstring zsh,$(shell echo $$SHELL)),zsh)
rc_file = ~/.zshrc
else ifeq ($(findstring bash,$(shell echo $$SHELL)),bash)
rc_file = ~/.bashrc
else
# assume bash shell if no match - needed for BuildJet CI runners which use various shell values like '2740SHELL'
rc_file = ~/.bashrc
endif
auto-setup: activate-service-account get_index_url
	echo 'export UV_EXTRA_INDEX_URL=$(index_url)\n' >> $(rc_file)
