# phony targets are targets that don't actually create a file
.phony: deploy-contract

# anvil's third default address
sender := 0x5de4111afa1a4b94908f83103eb1f1706367c2e68ca870fc3fb9a804cdab365a
signer := 0x70997970C51812dc3A010C7d01b50e0d17dc79C8
rpc_url := http://localhost:8545


# deploying the contract
deploy-contract:
	$(MAKE) run-forge-script script_name=Deploy script_contract_name=Deploy

run-forge-script:
	mkdir -p deployments
	forge build
	PRIVATE_KEY=$(sender) signer=$(signer) forge script \
	script/$(script_name).s.sol:$(script_contract_name) --broadcast --rpc-url $(rpc_url)
