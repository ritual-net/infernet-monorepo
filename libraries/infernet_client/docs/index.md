# Infernet Client

Infernet Client is a python library as well as a CLI tool. It allows you to:

1. Interact with the Infernet node's REST API.
2. Create an infernet wallet to make a payment for subscriptions, or to receive payments
via your infernet node for fulfilling the subscriptions.

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

To see all the available commands and options, head over to the [Usage](usage.md) documentation.

Consult [API Reference](reference/infernet_client/client.md) for detailed information on the available methods.
