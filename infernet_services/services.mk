toplevel_dir ?= infernet_services
service_dir ?= $(toplevel_dir)/services
deploy_dir ?= $(toplevel_dir)/deploy

build-service: get_index_url
	$(MAKE) build -C $(service_dir)/$(service) index_url=$(index_url)

run:
	$(MAKE) run -C $(service_dir)/$(service)

filename ?= "GenericCallbackConsumer.sol"
contract ?= "GenericCallbackConsumer"
coordinator ?= "0x5FbDB2315678afecb367f032d93F642f64180aa3"

service ?= hf_inference_client_service

deploy-contract:
	$(MAKE) deploy-contract -C $(toplevel_dir)/consumer-contracts \
		filename=$(filename) \
		coordinator=$(coordinator) \
		contract=$(contract)

save-image:
	docker save ritualnetwork/$(service):latest -o $(service).tar

env ?= '{"HF_INF_TASK": "text_generation", "HF_INF_MODEL": "HuggingFaceH4/zephyr-7b-beta"}'

deploy-node:
	[ -n "$$create_config" ] && \
	jq '.containers[0].env = $(shell echo $(env))' \
	$(service_dir)/$(service)/config.json > $(deploy_dir)/config.json || true
	docker-compose -f $(deploy_dir)/docker-compose.yaml up -d

swap-service:
	docker kill $(service) infernet-node || true
	docker rm $(service) infernet-node || true
	$(MAKE) deploy-node

stop-node:
	@docker compose -f $(deploy_dir)/docker-compose.yaml kill || true
	@docker compose -f $(deploy_dir)/docker-compose.yaml rm -f || true
	@docker stop $(service) anvil-node || true
	@docker rm $(service) anvil-node || true
	@kill $(lsof -i :8545 | grep anvil | awk '{print $2}') || true

filter ?= ""

test-service: stop-node
	# kill anything running on 3000
	kill $(lsof -i :3000 | tail -n 1  | awk '{print $2}') || true
	pytest -vvv -s $(toplevel_dir)/tests/$(service)

dev: build-service stop-node deploy-node
	sleep 5
	$(MAKE) deploy-contract

update-lock:
	uv venv && source .venv/bin/activate && \
	uv pip install -r $(toplevel_dir)/$(req_file).txt && \
	uv pip freeze > $(toplevel_dir)/$(req_file).lock

open-terminal:
	osascript -e 'tell app "Terminal" to do script "$(command)"'
