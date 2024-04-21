# Infernet Monorepo

This monorepo includes all of the libraries & frameworks used for building & running containers in Infernet Nodes.

## Overview

Currently, the structure is as follows:

```
├── Makefile
├── README.md
├── projects
│ ├── infernet_ml
│ └── ritual_arweave
│ └── (etc.)
├── pyproject.toml
├── requirements-dev.lock
└── requirements.lock
```

* `projects/`: This directory contains all of the python projects. Currently, the `infernet_ml` library has been ported
  over from its own standalone repo to here. Other python projects to be included here are: `ritual-arweave`,
  `ritual-celestia`, `infernet-client` & `ritual-pyarweave`.
* `pyproject.toml`: This is the top-level `pyproject.toml` that is primarily used by [`rye`](https://rye-up.com/) (see
  below). This is akin to the top-level `package.json` file in JS monorepos.

## Structure of Python Projects

This repository was scaffolded using [`rye`](https://rye-up.com/). Rye comes with built-in support for packaging &
installing python packages. It also has support for [workspaces](https://rye-up.com/guide/workspaces/), which allows us
to follow a monorepo structure where we have multiple python libraries in the same repository.

### Python Projects

Each project is listed under the `projects/` directory along with its own `pyproject.toml`.

To create a new python project use `rye init`:

```bash
cd projects # navigate to the projects directory
rye init myproject
```

If your project has an executable:

```bash
rye init --script myprojet
```

This will set up the project such that upon installation, the project is packaged as a binary that can be run from the
commandline. Libraries like `flask` are packaged in such way, where you can both use their packages in your python code,
and also use their binary from your commandline.

Such a structure is useful for projects like `ritual_pyarweave`, where you can both use the library to connect to
Arweave, as well as use the commandline tool to upload a file directly to Arweave without having to write code.

### Build System

Rye by default uses [`hatchling`](https://github.com/pypa/hatch) for packaging & creation of the libraries.

### Package Management

Rye can work both with `pip` and `uv`. Default is `pip`.

To configure Rye to use `uv`, run:

```bash
rye config --set-bool default.use-uv=true
```

## Prerequisites

* [Rye](https://rye-up.com/guide/installation/).
* [GCloud CLI](https://cloud.google.com/sdk/docs/install).

## Building a Library

To build a library run:

```bash
make build project=$(library_name)
```

`library_name` here should match the directory name of the library under `projects/`.

## GCP Setup

This repo comes with utility Make commands for building & publishing the python packages to a python index hosted on
GCP.

### Create a Python Artifact Repository

First, log into your Google Cloud Console dashboard & create a python artifact registry.

### Set up environment vars

Copy over the sample file to `gcp.env`

```
cp gcp.env.sample gcp.env
```

Set the following environment variables:

* `artifact_repo`: name of the artifact repository that contains your pypi index.
* `artifact_location`: location of the artifact repository
* `gcp_project`: name of your GCP project
* `sa_name`: name of the service account that will have read/write access to the artifact registry. This is used for
  both installing packages from the artifact registry as well as publishing packages to it.

### Setting up a Service Account & Correct Permissions

Note that you only need to run the following commands only once. After making a service account you an simply use it
upon future clonings of this repo.

Log in to `gcloud`.

```bash
gcloud auth login
```

#### Make a Service Account

```bash
make create-service-account
```

This will create a service account with the same name you've provided in the `gcp.env` file.

#### Grant Permissions

```bash
make grant-permissions
```

#### Get the Auth File

To get the auth file for that service account, simply run:

```bash
make get-auth-file
```

This will create a file named `$(sa_name)-key.json` where `sa_name` is the name of your service account.

#### Activate the Service Account

This is used in CI to ensure publishing & installation.

```
make activate-service-account
```

## Publish A Package to GCP

First, ensure that you've either logged in via `gcloud` cli, or that you have pulled the auth file for the service
account & have activated it.

Then you can run:

```
make publish project=$(library_name)
```

`library_name` here should match the directory name of the library under `projects/`.

### Troubleshooting Publishing Packages
1. **Package Version**: You can't overwrite a version when publishing to the pypi repository. Either bump the minor
version, or bump the `build tag`, that means following the version with a `-` and a digit i.e. `0.1.0-3`.
