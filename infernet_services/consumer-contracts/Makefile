# phony targets are targets that don't actually create a file
.phony: deploy-contract

# anvil's third default address
sender := 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a
rpc_url := http://localhost:8545

# deploying the contract
deploy-contract:
	mkdir -p deployments
	forge build
	PRIVATE_KEY=$(sender) forge script \
	script/Deploy.s.sol:Deploy --broadcast --rpc-url $(rpc_url)
