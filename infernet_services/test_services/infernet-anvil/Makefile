.phony: deploy-contract

# anvil's third default address
sender := 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a
rpc_url := http://localhost:8545
state_file := infernet_deployed.json
# anvil's second default address
node_address := 0x70997970C51812dc3A010C7d01b50e0d17dc79C8

# deploying the contract
deploy-infernet:
	forge build
	PRIVATE_KEY=$(sender) \
	payment_wallet_owner=$(node_address) \
	forge script \
	script/DeployInfernet.s.sol:DeployInfernet --broadcast --rpc-url $(rpc_url)

start-anvil:
	rm anvil.pid anvil.log || true
	# get the PID & save it to a file
	anvil --dump-state $(state_file) 2>&1 > anvil.log & \
	echo $$! > anvil.pid

watch-logs:
	tail -f anvil.log

stop-anvil:
	kill -2 `cat anvil.pid`

leave-running:
	$(MAKE) start-anvil
	$(MAKE) deploy-infernet

generate-state-file:
	rm $(state_file) || true
	$(MAKE) start-anvil
	$(MAKE) deploy-infernet
	$(MAKE) stop-anvil

tag := 1.0.0
img_name := ritualnetwork/infernet-anvil:$(tag)

build: generate-state-file
	docker build -t $(img_name) .

run:
	docker run -it --rm --name infernet-anvil -p 8545:3000 $(img_name)

registry := 0x663F3ad617193148711d28f5334eE4Ed07016602
coordinator_address := 0x2E983A1Ba5e8b38AAAeC4B440B9dDcFBf72E15d1
inbox_address := 0x8438Ad1C834623CfF278AB6829a248E37C2D7E3f
reader_address := 0xBC9129Dc0487fc2E169941C75aABC539f208fb01
fee_address := 0x6e989C01a3e3A94C973A62280a72EC335598490e
wallet_factory_address := 0xF6168876932289D073567f347121A267095f3DD6
wallet_address := 0x60985ee8192B322c3CAbA97A9A9f7298bdc4335C

check-contracts-exist:
	cast co $(registry)
	cast co $(coordinator_address)
	cast co $(inbox_address)
	cast co $(reader_address)
	cast co $(fee_address)
	cast co $(wallet_factory_address)
	cast co $(wallet_address)

# You may need to set up a docker builder, to do so run:
# docker buildx create --name mybuilder --bootstrap --use
# refer to https://docs.docker.com/build/building/multi-platform/#building-multi-platform-images for more info
build-multiplatform: generate-state-file
	docker buildx build --platform linux/amd64,linux/arm64 -t $(img_name) --push .
