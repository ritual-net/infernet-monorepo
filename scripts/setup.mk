ifeq ("$(wildcard .env)","")
$(warning "⚠️WARNING: no .env file found, some of these commands may fail⚠️")
else
include .env
endif

ifeq ("$(wildcard pypi-deployer-key.json)","")
$(warning "⚠️WARNING: no pypi-deployer-key.json file found, some of these commands may fail⚠️")
endif

GCP_PROJECT := private-pypi-418615

init-repo:
	@echo "🚀 initializing repo";
	@echo "ℹ️ If this command fails, please make sure you have authenticated with gcloud by running 'gcloud auth login'";
	@if [ -z "$$CI" ]; then \
		gcloud config set project $(GCP_PROJECT); \
	fi; \
	make pull-secrets

add-secret:
	@if gcloud secrets list | grep -q $(name); then \
		echo "secret $(name) already exists"; \
	else \
		gcloud secrets create $(name) --replication-policy="automatic"; \
	fi; \
	gcloud secrets versions add $(name) --data-file=$(file)

add-secrets:
	@make add-secret name=env-file file=".env"
	@make add-secret name=pypi-key file="pypi-deployer-key.json"

pull-secret:
	@if gcloud secrets list --project $(GCP_PROJECT) | grep -q $(name); then \
		echo "ℹ️ pulling secret $(name) to $(file)"; \
		gcloud secrets versions access latest --project $(GCP_PROJECT) --secret=$(name) > $(file); \
	else \
		echo "secret $(name) not found"; \
	fi

pull-secrets:
	@make pull-secret name=env-file file=".env"
	@make pull-secret name=pypi-key file="pypi-deployer-key.json"

create-secrets-sa:
	@echo "🚀 creating service account secrets-sa"
	@gcloud iam service-accounts create secrets-sa --display-name="Infernet Monorepo Secrets SA"
	@gcloud projects add-iam-policy-binding $(GCP_PROJECT) --member="serviceAccount:secrets-sa@$(GCP_PROJECT).iam.gserviceaccount.com" --role="roles/secretmanager.secretAccessor"
	@gcloud projects add-iam-policy-binding $(GCP_PROJECT) --member="serviceAccount:secrets-sa@$(GCP_PROJECT).iam.gserviceaccount.com" --role="roles/secretmanager.viewer"
	@gcloud iam service-accounts keys create secrets-sa-key.json --iam-account=secrets-sa@$(GCP_PROJECT).iam.gserviceaccount.com
