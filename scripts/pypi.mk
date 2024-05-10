# Make commands for building python packages & publishing them to GCP's Artifact Registry
SHELL := /bin/bash

# Conditional assignment based on the operating system
ifeq ($(shell uname -s),Darwin)
    SED := gsed
else
    SED := sed
endif

# setting the python project version.
# modifies the pyproject.toml file for the project at projects/$(project)
set-version:
	$(SED) -i 's/version = .*/version = "$(version)"/' projects/$(project)/pyproject.toml

build-library:
	rye build --pyproject projects/$(project)/pyproject.toml

repository_url := https://$(artifact_location)-python.pkg.dev/$(gcp_project)/$(artifact_repo)/

# twine oauth2 username
username := _token

# Gets the service account's credentials & sets them
get_index_url:
	$(eval token := $(shell gcloud auth print-access-token))
	$(eval index_url := "https://_token:$(token)@$(artifact_location)-python.pkg.dev/$(gcp_project)/$(artifact_repo)/simple")

show-token: get_index_url
	@echo $(token)

show-index-url: get_index_url
	@echo $(index_url)

# explicit install command to test uv installation
uv-install: get_index_url
	uv venv; \
	source .venv/bin/activate; \
	uv pip install --index-url https://pypi.org/simple --extra-index-url $(index_url) $(project)

# explicit install command to test pip installation
pip-install: get_index_url
	pip install --index-url https://pypi.org/simple --extra-index-url $(index_url) $(project)

# utility to create, install & activate an environment
setup-env:
	uv venv && source .venv/bin/activate && uv pip install -r projects/$(project)/requirements.lock

# updates the python lockfile of the specific project
update-lockfile:
	make -C projects/$(project) update-lockfile

publish: get_index_url
	rye publish --repository ritual-pypi \
		--repository-url $(repository_url) \
		--username $(username) \
		--token $(token) \
		--yes \
		--verbose \
	 	dist/$$(ls dist | grep "$(project).*.tar.gz")

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

generate-uv-env-file: get_index_url
	@echo "UV_EXTRA_INDEX_URL=$(index_url)" > uv.env

ifeq ($(findstring zsh,$(shell echo $$SHELL)),zsh)
rc_file = ~/.zshrc
else ifeq ($(findstring bash,$(shell echo $$SHELL)),bash)
rc_file = ~/.bashrc
else
$(error Unknown shell)
endif
auto-setup: activate-service-account get_index_url
	echo 'export UV_EXTRA_INDEX_URL=$(index_url)\n' >> $(rc_file)
