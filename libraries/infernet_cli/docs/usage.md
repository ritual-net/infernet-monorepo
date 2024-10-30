# Usage

The following examples assume a target directory `deploy/`. All files related to node configuration and deployment will be stored here.

You can set the target directory with every command using `--dir`, or you can set it once as an ENV variable:

```bash
export DEPLOY_DIR=deploy
```

## Node Configuration

To pull plug-and-play node configurations, you can use `config`.

<details>
    <summary>Usage</summary>
    ```
    Usage: infernet-cli config [OPTIONS] {anvil|base|base-sepolia|eth|other}

      Pull node configurations.

    Options:
      -v, --version TEXT  The version of the node to configure.
      -d, --dir TEXT      The directory to store and retrieve configuration files.
                        Can also set DEPLOY_DIR environment variable.
      --gpu               Enable GPU support for the node.
      -i, --inputs TEXT   The inputs to fill in the recipe. Should be a JSON
                        string of key-value pairs. If not provided, the user
                        will be prompted for inputs via the CLI.
      -y, --yes           Force overwrite of existing configurations.
      --skip              Skip optional inputs.
    ```
</details>

**Example**:

```bash
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

Notice that for demonstration purposes, we are using the `--skip` flag to default optional inputs.

### Inputs

Depending on your chain selection, some configuration will need user input in real time. For example, when configuring a node for `Base Mainnet`, user will be prompted for their wallet's `private_key` and an optional `payment_address`.

```bash
infernet-cli config base
```

The output will look something like the following. First, you will be prompted for a **required** input, the `private_key`:

```
No version specified. Using latest: v1.3.0
Using configurations:
   Chain = 'base'
   Version = '1.3.0'
   GPU support = disabled
   Output dir = 'deploy'
"private_key" (string): Private key for the wallet (Required):
    Enter value:
```

You should enter your private key followed by the `return` key. Next, you'll be prompted for an optional `payment_address`:

```
"payment_address" (string): Payment address for the wallet (RETURN to skip):
    Enter value:
```

Assuming you don't need to accept payments just yet, you can simply skip it by hitting `return`. You should then see output similar to the following:

```
Stored base configurations to '/root/deploy'.
To configure services:
  - Use `infernet-cli add-service`
  - Or edit config.json directly
```

**Alternatively**, the same inputs can be provided **non-interactively** as a JSON string, using the `--inputs` option:

```bash
infernet-cli config base -v "1.3.0" --inputs '{"private_key": "0xxxxxxxxxx"}'
# Same as above
```

### GPU

To deploy a GPU-enabled Infernet Node, just use the `--gpu` flag. This assumes your machine is GPU-enabled.

```bash
infernet-cli config base --gpu --inputs '{"private_key": "0xxxxxxxxxx"}'
```

The output will look something like this:

```
Using configurations:
   Chain = 'base'
   Version = '1.3.0'
   GPU support = enabled
   Output dir = 'deploy'

Stored base configurations to '/root/deploy'.
To configure services:
  - Use `infernet-cli add-service`
  - Or edit config.json directly
```

## Service Configuration

To add service containers to the node, you can use `add-service`.

You can configure a service either [manually](#manually) by providing a complete [container specification](https://docs.ritual.net/infernet/node/configuration/v1_2_0#container_spec-object), or using [recipes](#recipes).

<details>
    <summary>Usage</summary>
    ```
    Usage: infernet-cli add-service [OPTIONS] [RECIPE_ID]

      Add a service to the node configuration.

    Options:
      -d, --dir TEXT     The directory to store and retrieve configuration files.
                        Can also set DEPLOY_DIR environment variable.
      -i, --inputs TEXT  The inputs to fill in the recipe. Should be a JSON string
                        of key-value pairs. If not provided, the user will be
                        prompted for inputs via the CLI.
      --skip             Skip optional inputs.
    ```
</details>

### Recipes

You can configure one or more [official Ritual services](https://infernet-services.docs.ritual.net) using our pre-configured [service recipes](https://github.com/ritual-net/infernet-recipes/tree/main/services).

```bash
infernet-cli add-service hf-client-inference:1.0.0
```

Similar to config [inputs](#inputs), you will be prompted for configuration parameters:

```
"HF_TOKEN" (string): The Hugging Face API token. (Required):
    Enter value:
```

and

```
"NUM_WORKERS" (integer): The number of workers to use with the server. (RETURN to skip):
    Enter value:
```

Notice that `HF_TOKEN` is required, but `NUM_WORKERS` can be skipped. You should expect to see the following output:

```
Successfully added service 'hf-client-inference:1.0.0' to config.json.
```

**Alternatively**, the same inputs can be provided **non-interactively** as a JSON string, using the `--inputs` option:

```bash
infernet-cli add-service hf-client-inference:1.0.0 --inputs '{"HF_TOKEN": "a0xxxxxxxxxxxxx"}'
```

### Manually

You can also add custom service configurations via command-line:

```bash
infernet-cli add-service
```

You will be prompted to paste an entire service configuration:

```bash
Enter service configuration JSON, followed by EOF:
```

To configure an identical service as [above](#recipes), you can paste the following:

```
{
    "id": "hf-client-inference",
    "image": "ritualnetwork/torch_inference_service:1.0.0",
    "env": {"HF_TOKEN": "a0xxxxxxxxxxxxx"},
    "command": "--bind=0.0.0.0:3000 --workers=2"
}
```

followed by EOF (`Ctrl+D` on Linux / MacOS). You should see output similar to this:

```
Successfully added service 'hf-client-inference' to config.json.
```

### Remove

You can remove a service configuration with `remove-service`.

<details>
    <summary>Usage</summary>
    ```
    Usage: infernet-cli remove-service [OPTIONS] [SERVICE_ID]

      Remove a service from the node configuration.

    Options:
      -d, --dir TEXT  The directory to store and retrieve configuration files. Can
                    also set DEPLOY_DIR environment variable.
    ```
</details>

You can remove services **by ID**:

```bash
infernet-cli remove-service hf-client-inference:1.0.0
```

or remove all services:

```bash
infernet-cli remove-service
```

## Node Deployment

After [configuring a node](#node-configuration) and [adding some services](#service-configuration), you can manage its lifecycle as follows:

### Deploy

To **create** or **start** the node, use `start`.

<details>
    <summary>Usage</summary>
    ```
    Usage: infernet-cli start [OPTIONS]

      Start the Infernet Node.

    Options:
      -d, --dir TEXT  The directory to store and retrieve configuration files. Can
                    also set DEPLOY_DIR environment variable.
    ```
</details>

**Example:**

```bash
infernet-cli start
```

If successful, you should see:

```
# Starting Infernet Node...
# Containers started successfully.
```

### Health

To check the **health** of the node and containers, use `health`.

<details>
    <summary>Usage</summary>
    ```
    Usage: infernet-cli health [OPTIONS]

      Check health of the Infernet Node.

    Options:
      -d, --dir TEXT  The directory to store and retrieve configuration files. Can
                    also set DEPLOY_DIR environment variable.
    ```
</details>

**Example:**

```bash
infernet-cli health
```

If successful, you should see:

```
All containers are up and running.
```

### Stop

To stop the node, use `stop`.

<details>
    <summary>Usage</summary>
    ```
    Usage: infernet-cli stop [OPTIONS]

      Stop the Infernet Node.

    Options:
      -d, --dir TEXT  The directory to store and retrieve configuration files. Can
                    also set DEPLOY_DIR environment variable.
    ```
</details>

**Example:**

```bash
infernet-cli stop
```

If successful, you should see:

```
Stopping Infernet Node...
Containers stopped successfully.
```

### Reset

To reset the node, use `reset`.

<details>
    <summary>Usage</summary>
    ```
    Usage: infernet-cli reset [OPTIONS]

      Reset Infernet Node.

    Options:
      -d, --dir TEXT  The directory to store and retrieve configuration files. Can
                    also set DEPLOY_DIR environment variable.
      --services      Force removal of service containers. Destructive operation.
    ```
</details>

**Example:**

```bash
infernet-cli reset
```

If successful, you should see:

```
Resetting Infernet Node...
Containers stopped successfully.
Containers started successfully.
```

By default, service containers are **not** reset when the node is stopped or destroyed. This is intended behavior to ensure pre-processing-heavy services are not repeatedly initialized. To **force** reset all service containers, use the `--services` flag. This is a destructive operation:

```bash
infernet-cli reset --services
```

If successful, you should see:

```
Resetting Infernet Node...
Containers stopped successfully.
Destroying service containers...
Containers started successfully.
```

### Destroy

To destroy the node, use `destroy`.

<details>
    <summary>Usage</summary>
    ```
    Usage: infernet-cli destroy [OPTIONS]

      Destroy the Infernet Node.

    Options:
      -d, --dir TEXT  The directory to store and retrieve configuration files. Can
                    also set DEPLOY_DIR environment variable.
      --services      Force removal of service containers. Destructive operation.
      -y, --yes       No manual y/n confirmation required.
    ```
</details>

**Example:**

```bash
infernet-cli destroy -y
```

If successful, you should see:

```
Destroying Infernet Node...
Containers stopped successfully.
Containers destroyed successfully.
```

By default, service containers are **not** destroyed when the node is stopped or destroyed. This is intended behavior to ensure pre-processing-heavy services are not repeatedly initialized. To **force** destroy all service containers, use the `--services` flag. This is a destructive operation:

```bash
infernet-cli destroy --services -y
```

If successful, you should see:

```
Destroying Infernet Node...
Containers stopped successfully.
Containers destroyed successfully.
Destroying service containers...
```
