include gcp.env

SHELL := /bin/bash

# service account email
sa_email := $(sa_name)@$(gcp_project).iam.gserviceaccount.com
# service account auth file name
keyfile_name := $(sa_name)-key.json

clean:
	rm -rf dist

# Conditional assignment based on the operating system
ifeq ($(shell uname -s),Darwin)
    SED := gsed
else
    SED := sed
endif

set-version:
	$(SED) -i 's/version = .*/version = "$(version)"/' projects/$(project)/pyproject.toml

build:
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
activate-env:
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
	@echo "export UV_EXTRA_INDEX_URL=$(index_url)" >> uv.env

ifeq ($(findstring zsh,$(shell echo $$SHELL)),zsh)
rc_file = ~/.zshrc
else ifeq ($(findstring bash,$(shell echo $$SHELL)),bash)
rc_file = ~/.bashrc
else
$(error Unknown shell)
endif
auto-setup: activate-service-account get_index_url
	echo 'export UV_EXTRA_INDEX_URL=$(index_url)\n' >> $(rc_file)

# Service account creation and permissions (this is typically only done once)
# create the service account
create-service-account:
	gcloud iam service-accounts create $(sa_name) --display-name="Ritual Pypi Deployer"

# delete the service account
delete-service-account:
	gcloud iam service-accounts delete $(sa_email) -q

# gives a specific role to the service account
give-role:
	gcloud artifacts repositories add-iam-policy-binding $(artifact_repo) \
		--location=$(artifact_location) \
		--project=$(gcp_project) \
		--member=serviceAccount:$(sa_name)@$(gcp_project).iam.gserviceaccount.com \
		--role=$(role)

# grant the service account permissions to read from & write to the artifact registry
grant-permissions:
	$(MAKE) give-role role=roles/artifactregistry.writer
	$(MAKE) give-role role=roles/artifactregistry.reader

# get service account auth file
get-auth-file:
	gcloud iam service-accounts keys create $(keyfile_name) \
		--iam-account=$(sa_name)@$(gcp_project).iam.gserviceaccount.com

# to get the keyfile, first run get-auth-file
activate-service-account:
	gcloud auth activate-service-account --key-file=$(keyfile_name)

# export auth file to base64
export-auth-file:
	base64 -i $(keyfile_name) -o $(keyfile_name).b64
