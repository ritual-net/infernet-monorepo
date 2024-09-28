# Infernet Monorepo

This monorepo includes all of the libraries & frameworks used for building & running containers in Infernet Nodes.

## Overview

Currently, the repository structure is as follows (not all files / directories are shown):

* `infernet_services/`: Infernet-compatible containers and tests.
  * `consumer-contracts/`: Contracts used for onchain (web3) testing.
  * `deploy/`: Deployment files for test Nodes.
  * `services/`: Source code for containers.
    * `css_inference_service/`
    * `ezkl_proof_service/`
    * `css_inference_service/`
    * `hf_inference_client_service/`
    * `onnx_inference_service/`
    * `tgi_client_inference_service/`
    * `torch_inference_service/`
  * `test_services/`: Source code for testing-only containers, such as the local `Anvil` chain instance.
  * `tests`: Source code for container tests, Node E2E tests, and common `test_library`.
* `libraries/`: All of the Python libraries.
  * `infernet_ml/`: Source code for the `infernet-ml` library.
  * `infernet_cli`: Source code for the `infernet-cli` library & CLI tool.
  * `infernet_client/`: Source code for the `infernet-client` library & CLI tool.
  * `ritual_arweave/`: Source code for the `ritual-arweave` library & CLI tool.
  * `infernet_pyarweave/`: Source code for the `infernet-pyarweave` library.
* `scripts/`: Makefile scripts used for publishing packages, deploying
  services, generating docs, etc.
* `tools/`: Miscellaneous scripts used for auto-generation and deployment
  of library and service documentation pages.
* `pyproject.toml`: Top-level `pyproject.toml` primarily used by [`rye`](https://rye-up.com/) to handle various tasks regarding monorepo management. This is akin to the top-level `package.json` file in JS monorepos.

## Development

### Pre-requisites

To develop in the monorepo, we suggest you pre-install the following in advance:

* [Python 3.11](https://www.python.org/downloads/) (older versions might work)
* [Docker](https://docs.docker.com/desktop/)
* [uv](https://github.com/astral-sh/uv?tab=readme-ov-file#getting-started)
* [fzf](https://github.com/junegunn/fzf)

### Deployer Key

_Only applies to the Ritual team._

For publishing libraries to the Ritual PyPi repository, you will need a service account with access to our private GCP project. Ask the team to provide you with a `pypi-deployer-key.json` file, or access to create one yourself. Place the file in the top-level directory of this repository.

### Secrets

_Only applies to the Ritual team._

To test [libraries](#python-libraries) and [services](#services), you will need a `.env` file with secrets.

First, authenticate with the `gcloud` CLI. Run
```bash copy
gcloud auth login
```
and follow the steps in your browser. Then, initialize the repository:
```bash copy
make init-repo
```
If successful, you should now see the `.env` file in the top-level directory of this repository.

## Python Libraries

The `libraries/` portion of this repository was scaffolded using [`rye`](https://rye-up.com/). Rye comes with built-in support for packaging & installing python packages. It also has support for [workspaces](https://rye-up.com/guide/workspaces/), which allows us to follow a monorepo structure where we have multiple python libraries in the same repository.

For installation and usage documentation of the libraries, please refer to:

1. [infernet-cli](https://infernet-cli.docs.ritual.net/)
2. [infernet-client](https://infernet-client.docs.ritual.net/)
3. [infernet-ml](https://infernet-ml.docs.ritual.net/quickstart/)
4. [ritual-arweave](https://ritual-arweave.docs.ritual.net/quickstart/)

The following sections detail how to develop, build, and test the Python libraries.

### Development setup

If developing on a library or running tests, you can set up the development environment by running:

```bash
make setup-library-env
```

This will create a new `uv` environment under the `.venv` directory. Activate it by running:

```bash
source .venv/bin/activate
```

If modifying the dependencies in a library's  `pyproject.toml` (or to simply bump third-party library versions), you can update the `requirements.lock` file with:

```bash
make update-library-lockfile
```

### Testing

You can run tests for a library as follows:

```bash
make test-library
```

You can run the `pre-commit` scripts for a library as follows:

```bash
make pre-commit-library
```

### Building

You can build a library by running:

```bash
make build-library
```

This will create a `dist` folder and a `.tar.gz` file for the library.

**Build System:** Rye by default uses [`hatchling`](https://github.com/pypa/hatch) for packaging & creation of the libraries.

### Publishing

To publish a library, you can run:

```bash
make publish-library
```

Note that you would need a `pypi` account and a [key](#deployer-key) to be able to publish a library.

## Services

All of the services are located in the `infernet_services` directory. These services are Infernet-compatible containers that work out-of-the-box, and cover many of the common use-cases for ML workflows.

For documentation on the services & how to use them, please refer to the [Infernet Services Documentation](https://infernet-services.docs.ritual.net/). The following sections detail how to develop, build, and test the Infernet Services.

### Development setup

If developing on a service or running tests, you can set up the development environment by running:

```bash
make setup-services-test-env
```

This will create a new `uv` environment under the `.venv` directory. Activate it by running:

```bash
source .venv/bin/activate
```

If modifying the dependencies in a service's `requirements.txt` (or to simply bump third-party library versions), you can update the `requirements.lock` file with:

```bash
make update-service-lockfile
```

### Testing

You can run tests for a service as follows:

```bash
make test-service
```

You can run the `pre-commit` scripts for a service as follows:

```bash
make pre-commit-service
```

### Building

You can build a service's Docker image as follows:

```bash
make build-service
```

### Running

To run a service, we suggest you configure & deploy it via an Infernet Node. This is very similar to how [testing](#testing-1) a service is set up, except you have full control the node and container configurations.

#### Configure the service
Create a `config.json` file under the `infernet_services/deploy` directory. To learn about the possible config params, refer to [the configuration documentation](https://docs.ritual.net/infernet/node/configuration).

**Hint**: You can start by manually creating the `config.json` used for [testing](#testing-1), and then proceed to modify it. To do so, run

```bash
PYTHONPATH=infernet_services/tests python infernet_services/tests/<service_name>/conftest.py
```

replacing `<service_name>` with the name of the service you are configuring.

#### Deploy the node

```bash
make deploy-node
```

This should deploy the Infernet Node on port `4000`, as well as the configured services in `config.json`. We recommend using Docker Desktop to monitor and manage containers.
