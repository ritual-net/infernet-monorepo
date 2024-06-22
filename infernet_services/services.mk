toplevel_dir ?= infernet_services
service_dir ?= $(toplevel_dir)/services
deploy_dir ?= $(toplevel_dir)/deploy

build-service:
	$(MAKE) build -C $(service_dir)/$(service) index_url=$(index_url)

publish-service:
	$(MAKE) build-multiplatform -C $(service_dir)/$(service) index_url=$(index_url)

run:
	$(MAKE) run -C $(service_dir)/$(service)

filename ?= "GenericCallbackConsumer.sol"
contract ?= "GenericCallbackConsumer"
registry ?= "0x663F3ad617193148711d28f5334eE4Ed07016602"

deploy-contract:
	$(MAKE) deploy-contract -C $(toplevel_dir)/consumer-contracts \
		filename=$(filename) \
		registry=$(registry) \
		contract=$(contract)

deploy-everything:
	$(MAKE) run-forge-script script_name=Deploy script_contract_name=DeployEverything

run-forge-script:
	$(MAKE) run-forge-script -C $(toplevel_dir)/consumer-contracts \
		registry=$(registry)

save-image:
	docker save ritualnetwork/$(service):latest -o $(service).tar

env ?= '{"HF_INF_TASK": "text_generation", "HF_INF_MODEL": "HuggingFaceH4/zephyr-7b-beta"}'

deploy-node:
	[ -n "$$create_config" ] && \
	jq '.containers[0].env = $(shell echo $(env))' \
	$(service_dir)/$(service)/config.json > $(deploy_dir)/config.json || true
	docker-compose -f $(deploy_dir)/docker-compose.yaml up -d

start-infernet-anvil:
	docker-compose -f $(deploy_dir)/docker-compose.yaml up -d infernet-anvil

stop-infernet-anvil:
	docker-compose -f $(deploy_dir)/docker-compose.yaml kill infernet-anvil || true
	docker-compose -f $(deploy_dir)/docker-compose.yaml rm -f infernet-anvil || true

stop-service:
	services=`docker ps -aq --filter "name=$(service)*"` && \
	docker kill $$services || true && \
	docker rm $$services || true

setup-services-test-env:
	uv venv -p 3.11 && \
	source .venv/bin/activate && \
	$(MAKE) generate-uv-env-file && source uv.env && \
	uv pip install -r infernet_services/requirements-e2e-tests.lock

swap-service: stop-service
	docker kill infernet-node || true && docker rm infernet-node || true
	$(MAKE) deploy-node

stop-node:
	@docker compose -f $(deploy_dir)/docker-compose.yaml kill || true
	@docker compose -f $(deploy_dir)/docker-compose.yaml rm -f || true
	@$(MAKE) stop-service || true
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

solc_version?=0.8.17

set-solc:
	solc-select use $(solc_version) --always-install

dev-mode:
	constants_path=`find infernet_services | grep test_lib | grep "constants\.py"`; \
	sed -i '' 's/skip_deploying = False/skip_deploying = True/' $$constants_path; \
	sed -i '' 's/skip_contract = False/skip_contract = True/' $$constants_path; \
	sed -i '' 's/skip_teardown = False/skip_teardown = True/' $$constants_path; \
	sed -i '' 's/suppress_logs = False/suppress_logs = True/' $$constants_path

prod-mode:
	constants_path=`find infernet_services | grep test_lib | grep "constants\.py"`; \
	sed -i.bak 's/skip_deploying = True/skip_deploying = False/' $$constants_path; \
	sed -i.bak 's/skip_contract = True/skip_contract = False/' $$constants_path; \
	sed -i.bak 's/skip_teardown = True/skip_teardown = False/' $$constants_path; \
	sed -i.bak 's/suppress_logs = True/suppress_logs = False/' $$constants_path
