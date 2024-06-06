## GCP Setup

This repo comes with utility Make commands for building & publishing the python packages
to a python index hosted on
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
* `sa_name`: name of the service account that will have read/write access to the artifact
  registry. This is used for
  both installing packages from the artifact registry as well as publishing packages to
  it.

### Setting up a Service Account & Correct Permissions

Note that you only need to run the following commands only once. After making a service
account you an simply use it
upon future clonings of this repo.

Log in to `gcloud`.

```bash
gcloud auth login
```

#### Make a Service Account

```bash
make create-service-account
```

This will create a service account with the same name you've provided in the `gcp.env`
file.

#### Grant Permissions

```bash
make grant-permissions
```

#### Get the Auth File

To get the auth file for that service account, simply run:

```bash
make get-auth-file
```

This will create a file named `$(sa_name)-key.json` where `sa_name` is the name of your
service account.

#### Activate the Service Account

This is used in CI to ensure publishing & installation.

```
make activate-service-account
```

## Publish A Package to GCP

First, ensure that you've either logged in via `gcloud` cli, or that you have pulled the
auth file for the service
account & have activated it.

Then you can run:

```
make publish project=$(library_name)
```

`library_name` here should match the directory name of the library under `libraries/`.

### Troubleshooting Publishing Packages

1. **Package Version**: You can't overwrite a version when publishing to the pypi
   repository. Either bump the minor
   version, or bump the `build tag`, that means following the version with a `-` and a
   digit i.e. `0.1.0-3`.
