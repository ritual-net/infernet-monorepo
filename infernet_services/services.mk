toplevel_dir ?= infernet_services
service_dir ?= $(toplevel_dir)/services
deploy_dir ?= $(toplevel_dir)/deploy

build-service: get_index_url
	$(MAKE) build -C $(service_dir)/$(service) index_url=$(index_url)

run:
	$(MAKE) run -C $(service_dir)/$(service)

filename ?= "GenericConsumerContract.sol"
contract ?= "GenericConsumerContract"

service ?= hf_inference_client_service

deploy-contract:
	$(MAKE) deploy-contract -C $(toplevel_dir)/consumer-contracts filename=$(filename) contract=$(contract)

save-image:
	docker save ritualnetwork/$(service):latest -o $(service).tar

env ?= '{"HF_INF_TASK": "text_generation", "HF_INF_MODEL": "HuggingFaceH4/zephyr-7b-beta"}'

deploy-node:
	jq '.containers[0].env = $(shell echo $(env))' $(service_dir)/$(service)/config.json > $(deploy_dir)/config.json
	docker-compose -f $(deploy_dir)/docker-compose.yaml up -d

stop-node:
	docker compose -f $(deploy_dir)/docker-compose.yaml kill || true
	docker compose -f $(deploy_dir)/docker-compose.yaml rm -f || true
	@docker stop $(service) anvil-node || true
	@docker rm $(service) anvil-node || true
	@kill $(lsof -i :8545 | grep anvil | awk '{print $2}') || true

filter ?= ""

run-tests: stop-node
	# kill anything running on 3000
	kill $(lsof -i :3000 | tail -n 1  | awk '{print $2}') || true
	pytest -vvv -s test/$(service)


dev: build stop-node deploy-node
	sleep 5
	$(MAKE) deploy-contract

update-lock:
	uv venv
	uv pip install -r $(req_file).txt
	uv pip freeze > $(req_file).lock

open-terminal:
	osascript -e 'tell app "Terminal" to do script "$(command)"'
