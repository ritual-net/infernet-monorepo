
# Infernet CLI

Infernet CLI is a tool that simplifies configuration and deployment of an [Infernet Node](https://github.com/ritual-net/infernet-node). Specifically, it enables:

1. Pulling plug-and-play [node configurations](https://github.com/ritual-net/infernet-recipes/tree/main/node) for different chains, with the ability to further configure and customize them.
2. Adding plug-and-play [service configurations](https://github.com/ritual-net/infernet-recipes/tree/main/services) to your node.
3. Creating, managing, and destroying a node.

## Prerequisites

- [Python >= 3.9](https://www.python.org/downloads/)
- [Docker Desktop](https://docs.docker.com/get-started/get-docker/) or ([Docker Engine](https://docs.docker.com/engine/install/) + [Docker Compose](https://docs.docker.com/compose/install/)).

## Installation
You can either install `infernet-cli` via [`uv`](https://astral.sh/blog/uv) (recommended) or via `pip`.

=== "uv"

    ``` bash
    uv pip install infernet-cli
    ```

=== "pip"

    ``` bash
    pip install infernet-cli
    ```

## Quickstart

Here's how you can **configure** a node connected to a local Anvil chain:

```bash
export DEPLOY_DIR=deploy/

infernet-cli config anvil --skip
```

The output will look something like this:

```
No version specified. Using latest: v1.3.0
Using configurations:
   Chain = 'anvil'
   Version = '1.3.0'
   GPU support = disabled
   Output dir = 'deploy'

Stored base configurations to '/root/deploy'.
To configure services:
  - Use `infernet-cli add-service`
  - Or edit config.json directly
```

You can add an ML service, e.g. `onnx-inference`, as follows:

```bash
infernet-cli add-service onnx-inference --skip
```

The output will look something like this:

```
Version not provided. Using latest version '2.0.0'.
Successfully added service 'onnx-inference-2.0.0' to config.json.
```

You can then **deploy** the node:

```bash
infernet-cli start
```

and check that it's **healthy**:

```bash
infernet-cli health
```

## More Options

To see all the available commands and options, head over to the [Usage](usage.md) documentation.
