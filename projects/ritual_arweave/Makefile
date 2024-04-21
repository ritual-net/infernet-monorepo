update-lockfile:
	uv venv && source .venv/bin/activate && \
	uv pip install -e ".[development]" -r pyproject.toml -U && \
	uv pip install -r pyproject.toml -U && \
	uv pip freeze | grep -v ritual_arweave > requirements.lock && rm -rf .venv

port ?= 3069
# starts arlocal, a local arweave server, useful for testing
start-arweave:
	@RUNNER=$$(command -v bunx || command -v npx); \
	if [ -z $$RUNNER ]; then \
		echo "Neither npx nor bunx found. Please install node."; \
		exit 1; \
	fi; \
	echo "Starting local arweave server using $$RUNNER..."; \
	$$RUNNER arlocal $(port)

seed ?= "test test test test test test test test test test test test"

# generates an arweave wallet
# more instructions here: https://docs.arweave.org/developers/wallets/generating-cold-wallet#cold-wallet-generation-with-the-ardrive-cli-advanced
generate-wallet:
	if [ -z ardrivee ]; then \
		echo "`ardrive` not installed, install it via: npm install -g ardrive-cli"; \
		exit 1; \
	fi;
	echo "Generating wallet..."
	ardrive generate-wallet -s $(seed) > ./wallet.json

# this is the default first test address generated from the `seed` variable above.
address ?= "9OtncJjXzqTWBlt26UHIGDxiD65GKGC2hdj6Mhai99g"
balance ?= 100000000000000

# mint some ar to the test wallet
fund:
	curl "http://127.0.0.1:$(port)/mint/$(address)/$(balance)"

# mine a block (required when working with arlocal)
mine:
	curl "http://127.0.0.1:$(port)/mine"
