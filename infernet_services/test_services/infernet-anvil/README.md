## Infernet Anvil

This is a simple anvil node docker image that has all of the infernet-sdk contracts
pre-deployed. This is useful for testing and development purposes.

### Contracts

The contracts have been deployed to the following addresses:

| Contract                 | Address                                      |
|--------------------------|----------------------------------------------|
| `Registry`               | `0x663F3ad617193148711d28f5334eE4Ed07016602` |
| `Coordinator Address`    | `0x2E983A1Ba5e8b38AAAeC4B440B9dDcFBf72E15d1` |
| `Inbox Address`          | `0x8438Ad1C834623CfF278AB6829a248E37C2D7E3f` |
| `Reader Address`         | `0xBC9129Dc0487fc2E169941C75aABC539f208fb01` |
| `Fee Address`            | `0x6e989C01a3e3A94C973A62280a72EC335598490e` |
| `Wallet Factory Address` | `0xF6168876932289D073567f347121A267095f3DD6` |
| `Wallet Address`         | `0x60985ee8192B322c3CAbA97A9A9f7298bdc4335C` |

The last row, `Wallet Address`, is the address of a wallet whose owner is anvil's
second default address: `0x70997970C51812dc3A010C7d01b50e0d17dc79C8`. This is provided
for convenience when testing an infernet-node along with some compute containers. In
a production environment, create your own wallet using the `WalletFactory` and use that
address.

### How it's built

Refer to the [`build`](./Makefile#L38) to see how this docker image is built:

First, a state file has been generated: [`make generate-state-file`](./Makefile#L29)

1. An anvil node is started: `make start-anvil`
2. The infernet-sdk contracts are deployed: `make deploy-infernet`
3. The anvil node is stopped: `make stop-anvil`. Uplon exit, anvil will save the state
   of the blockchain to a file: `infernet_deployed.json`.

Then, the docker image is built: `make build`.
