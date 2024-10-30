ifeq ("$(wildcard .env)","")
$(warning "⚠️WARNING: no .env file found, some of these commands may fail⚠️")
else
include .env
endif

ifeq ("$(wildcard pypi-deployer-key.json)","")
$(warning "⚠️WARNING: no pypi-deployer-key.json file found, some of these commands may fail⚠️")
endif

GCP_PROJECT ?= my-project

init-repo:
	@echo "🚀 initializing repo";
	@echo "ℹ️ If this command fails, please make sure you have authenticated with gcloud by running 'gcloud auth login'";
	@if [ -z "$$CI" ]; then \
		gcloud config set project $(GCP_PROJECT); \
	fi; \
	make pull-secrets
	make docker-login


submodule_sync_cmd := git -c protocol.version=2 submodule update --init --force \
	--depth=1 --recursive

get-submodules:
	$(submodule_sync_cmd) infernet_services/consumer-contracts/lib/better-deployer
	$(submodule_sync_cmd) infernet_services/consumer-contracts/lib/forge-std
	$(submodule_sync_cmd) infernet_services/consumer-contracts/lib/infernet-sdk
	$(submodule_sync_cmd) libraries/ritual_pyarweave/src
	$(submodule_sync_cmd) infernet_services/test_services/infernet-anvil/lib/forge-std
	$(submodule_sync_cmd) infernet_services/test_services/infernet-anvil/lib/infernet-sdk

GCLOUD := gcloud --project $(GCP_PROJECT)

add-secret:
	@if gcloud secrets list | grep -q $(name); then \
		echo "secret $(name) already exists"; \
	else \
		$(GCLOUD) secrets create $(name) --replication-policy="automatic"; \
	fi; \
	$(GCLOUD) secrets versions add $(name) --data-file=$(file)

add-secrets:
	@make add-secret name=env-file file=".env"
	@make add-secret name=pypi-key file="pypi-deployer-key.json"

version ?= latest
pull-secret:
	@if $(GCLOUD) secrets list | grep -q $(name); then \
		echo "ℹ️ pulling secret $(name) to $(file)"; \
		$(GCLOUD) secrets versions access $(version) --secret=$(name) > $(file); \
	else \
		echo "secret $(name) not found"; \
	fi

docker-login:
	@echo "ℹ️ Logging into docker"; \
	if [ -z "$(docker_username)" ] || [ -z "$(docker_password)" ]; then \
		echo "⚠️ No docker credentials found in .env, skipping docker login. You can add them by running 'make populate-env-with-docker-creds'"; \
		exit 0; \
	fi; \
	echo "$(docker_password)" | $(DOCKER) login -u $(docker_username) --password-stdin

pull-secrets:
	@make pull-secret name=env-file file=".env"
	@make pull-secret name=pypi-key file="pypi-deployer-key.json"

create-secrets-sa:
	@echo "🚀 creating service account secrets-sa"
	@gcloud iam service-accounts create secrets-sa --display-name="Infernet Monorepo Secrets SA"
	@gcloud projects add-iam-policy-binding $(GCP_PROJECT) --member="serviceAccount:secrets-sa@$(GCP_PROJECT).iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
	@gcloud projects add-iam-policy-binding $(GCP_PROJECT) --member="serviceAccount:secrets-sa@$(GCP_PROJECT).iam.gserviceaccount.com" --role="roles/secretmanager.viewer"
	@gcloud iam service-accounts keys create secrets-sa-key.json --iam-account=secrets-sa@$(GCP_PROJECT).iam.gserviceaccount.com

install-rye:
	curl -sSf https://rye.astral.sh/get | bash
