# Commands for managing GCP resources.
# Mainly consists of commands for service account creation in the context of the
# Artifact Registry. In summary, we create a service account, give it permissions
# to read from and write to the Artifact Registry, and some utility commands to
# get the service account auth file and export it to base64.
SHELL := /bin/bash

ifneq ("$(wildcard gcp.env)","")
include gcp.env
endif

# service account email
sa_email := $(sa_name)@$(gcp_project).iam.gserviceaccount.com
# service account auth file name
keyfile_name := $(sa_name)-key.json

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
