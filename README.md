# Infernet Monorepo

This monorepo includes all of the libraries & frameworks used for building & running
containers in Infernet Nodes.

## Overview

Currently, the structure is as follows:

```
├── Makefile
├── README.md
├── scripts
├── tools
├── infernet_services # contains out-of-the-box usable infernet services
├── projects
│ ├── infernet_ml # code for infernet-ml library
│ ├── infernet_client # code for infernet-client library & CLI tool
│ └── ritual_arweave # code for ritual-arweave library & CLI tool
│ └── infernet_pyarweave # code for ritual-pyarweave library
├── pyproject.toml
├── requirements-dev.lock
└── requirements.lock
```

* `libraries/`: This directory contains all of the python projects.
    * `infernet_ml/`: Contains the code for the `infernet-ml` library.
    * `infernet_client/`: Contains the code for the `infernet-client` library & CLI tool.
    * `ritual_arweave/`: Contains the code for the `ritual-arweave` library & CLI tool.
    * `infernet_pyarweave/`: Contains the code for the `infernet-pyarweave` library.
* `scripts/`: Contains various makefile scripts used for
    * `gcp.mk`: To use `gcloud` artifact repository for `pypi` packages.
    * `docs.mk`: To generate documentation for the python projects.
    * `pypi.mk`: To build & publish python packages.
* `tools/`: Contains miscellaneous scripts used across the monorepo. Currently it
  contains a `generate_docs.py` script
  that generates files from the python projects.
* `infernet_services/`: Contains the code for various useful-reusable Infernet
  services as well as end-to-end tests for them. It also contains `test_services` that
  are used to test the `infernet-node` in isolation.
* `pyproject.toml`: This is the top-level `pyproject.toml` that is primarily used
  by [`rye`](https://rye-up.com/) to handle various tasks regarding monorepo management.
  This is akin to the top-level `package.json` file in JS monorepos.

# Python Libraries

The `libraries/` portion of this repository was scaffolded
using [`rye`](https://rye-up.com/). Rye comes with built-in support for packaging &
installing python packages. It also has support
for [workspaces](https://rye-up.com/guide/workspaces/), which allows us
to follow a monorepo structure where we have multiple python libraries in the same
repository.

**Usage:**
For documentation on the libraries as well as how to install them, please refer to the
following links:

1. [`infernet-ml`](https://infernet-ml.docs.ritual.net/quickstart/)
2. [`ritual-arweave](https://ritual-arweave.docs.ritual.net/quickstart/)
3. [`infernet-client](https://infernet-client.docs.ritual.net/)

The following sections detail how to work with the python libraries in this repository.
That is how to build, test, and develop on them.

## Pre-requisites

* Python `3.11`
* Install [uv](https://github.com/astral-sh/uv?tab=readme-ov-file#getting-started).

## Overview of the commands

All of the commands follow the format

```bash
make <command> library=<library-name>
```

Where `<command>` is the name the command & `<library-name>` is the name of the
directory of the library.

For example, to run all the tests for the `infernet-ml` library, you would run:

```bash
make test-library library=infernet_ml
```

since the `infernet-ml` library is located in the `libraries/infernet_ml` directory.

## Set up development environment

If developing on a library or running tests, you can set up the development environment
by running:

```bash
make setup-library-env library=<library-name>
```

This will create a new `uv` environment under the `.venv` directory. Activate it by
running:

```
source .venv/bin/activate
```

## Running Tests for a Library

You can run tests for a library by running:

```bash
make test-library library=<library-name>
```

## Building a Library

Following in the same theme, you can build a library by running:

```bash
make build-library library=<library-name>
```

This will create a `dist` folder and a `.tar.gz` file for the library.

**Build System:** Rye by default uses [`hatchling`](https://github.com/pypa/hatch) for
packaging & creation
of the libraries.

### Publishing a Library

To publish a library, you can run:

```bash
make publish-library library=<library-name>
```

Note that you would need a `pypi` account and the necessary permissions to be able to
publish a library.

# Services

All of the services are located in the `infernet_services` directory. These services
are out-of-the-box reusable services that cover many of the common use-cases for
ML workflows.

For documentation on the services & how to use them, please refer to the
[Infernet Services Documentation](https://infernet-services.docs.ritual.net/).

For doing development on the services, you can follow the following sections.

## Pre-requisites

1. [Docker](https://docs.docker.com/desktop/)

## Overview of the commands

All of the commands follow the format

```bash
make <command> service=<service-name>
```

Where `<command>` is the name the command & `<service-name>` is the name of the
directory of the library.

For example, to run all the tests for the `css_inference_service` service, you would run:

```
make test-service service=css_inference_service
```

## Testing Services

You can run tests for a service by running:

```bash
make test-service service=<service-name>
```

## Building a Service

To build a service, you can run:

```bash
make build-service service=<service-name>
```

## Running Services

To run a service you would have to configure it & deploy it via an Infernet node.
To do so:

1. Create a `config.json` file under the `infernet_services/deploy` directory. To learn
   about the possible config params, refer
   to [the configuration documentation](https://docs.ritual.net/infernet/node/configuration/v1_1_0).
2. Run the following command:

```bash
make deploy-node service=<service-name>
```

This will deploy the service along with the Infernet node.
