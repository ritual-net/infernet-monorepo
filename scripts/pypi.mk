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
	rye build --pyproject libraries/$(library)/pyproject.toml

repository_url := https://$(artifact_location)-python.pkg.dev/$(gcp_project)/$(artifact_repo)/

# twine oauth2 username
username := _token

show-token:
	@echo $(token)

# explicit install command to test uv installation
uv-install:
	uv venv; \
	source .venv/bin/activate; \
	uv pip install --index-url https://pypi.org/simple --extra-index-url $(index_url) $(library)

# explicit install command to test pip installation
pip-install:
	pip install --index-url https://pypi.org/simple --extra-index-url $(index_url) $(library)

# utility to create, install & activate an environment
setup-env:
	uv venv && source .venv/bin/activate && uv pip install -r libraries/$(library)/requirements.lock

# updates the python lockfile of the specific library
update-lockfile:
	make -C libraries/$(library) update-lockfile

publish-library:
	rye publish --repository ritual-pypi \
		--repository-url $(repository_url) \
		--username $(username) \
		--token $(token) \
		--yes \
		--verbose \
	 	dist/$$(ls dist | grep "$(library).*.tar.gz")

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

get-index-url:
	@gcloud auth activate-service-account --key-file=pypi-deployer-key.json; \
	echo "https://_token:`gcloud auth print-access-token`@$(artifact_location)-python.pkg.dev/$(gcp_project)/$(artifact_repo)/simple"

generate-uv-env-file:
	index_url=`make get-index-url`; \
	echo "index url: $$index_url"; \
	echo "$(export_prefix)UV_EXTRA_INDEX_URL=$$index_url" > uv.env

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
