# Infernet Client

Welcome to the Infernet Client, a lightweight Python library and CLI tool that streamlines interaction with the [Infernet Node](https://github.com/ritual-net/infernet-node) and the [Infernet Router](https://github.com/ritual-net/infernet-router). The Infernet Node provides robust computational capabilities through a well-defined API, while the Router allows for discovering nodes and containers running remotely, across the Infernet network.

It also allows you to create and manage an Infernet Wallet is used for the [Payment System](https://docs.ritual.net/infernet/payments).

## Features

- **Simple**: Streamlined methods for interacting with the Infernet Node and Router APIs.
- **Asynchronous**: Built-in async capabilities for improved performance.
- **Typed**: Complete type annotations for better editor support and reduced bugs.


## Installation
You can either install `infernet-client` via [`uv` (Recommended)](https://astral.sh/blog/uv) or via `pip`.

=== "uv"

    ``` bash
    uv pip install infernet-client
    ```

=== "pip"

    ``` bash
    pip install infernet-client
    ```

## Quickstart

With your infernet node running, you can interact with it using either the CLI tool or the python library.

Here's how you can check the [server's health](https://docs.ritual.net/infernet/node/api#healthinfo):

=== "Python"

    ```python
    from infernet_client import NodeClient

    client = NodeClient("http://localhost:4000")
    is_healthy = await client.health()

    print(is_healthy)
    ```
    **Expected Output:**
    ```bash
    True
    ```

=== "CLI"

    ```bash
    export SERVER_URL=http://localhost:4000

    infernet-client health
    ```
    **Expected Output:**
    ```bash
    healthy
    ```

## More Options

You can view all options with `--help`:

```bash
infernet-client --help
# Usage: infernet-client [OPTIONS] COMMAND [ARGS]...
#
# Options:
#   --help  Show this message and exit.

# Commands:
#   approve        Approve a spender to spend a given amount of tokens.
#   containers     List containers running in the network
#   create-wallet  Create an Infernet Wallet.
#   find           Find nodes running the given containers
#   fund           Approve a spender to spend a given amount of tokens.
#   health         Health check
#   ids            Get job IDs for this client.
#   info           Get node information.
#   job            Request a job.
#   results        Fetch job results.
#   stream         Request a streamed job.
#   sub            Request a delegated subscription.
#   withdraw       Withdraw tokens.
```

To see documentation for all the available commands and options, head over to [Usage](usage.md).