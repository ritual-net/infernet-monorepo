# Infernet Client

Welcome to the Infernet Client, a lightweight Python library and CLI tool that streamlines interaction with the [Infernet Node](https://github.com/ritual-net/infernet-node) and the [Infernet Router](https://github.com/ritual-net/infernet-router). The Infernet Node provides robust computational capabilities through a well-defined API, while the Router allows for discovering nodes and containers running remotely, across the Infernet network.

This client aims to provide developers with a simple, efficient way to integrate and automate tasks using the Infernet [Node](#node) and [Router](#router).

## Features

- **Simple**: Streamlined methods for interacting with the Infernet Node and Router APIs.
- **Asynchronous**: Built-in async capabilities for improved performance.
- **Typed**: Complete type annotations for better editor support and reduced bugs.

## Installation

Install via [pip](https://pip.pypa.io/en/stable/):

```bash
pip install infernet-client
```

or [uv](https://pypi.org/project/uv/):
```bash
uv pip install infernet-client
```

## CLI

You can view all options with `--help`:

```bash
infernet-client --help
# Usage: infernet-client [OPTIONS] COMMAND [ARGS]...
#
# Options:
#   --help  Show this message and exit.

# Commands:
#   approve        Approve a spender.
#   check-model    Check model support.
#   containers     List containers running in the network
#   create-wallet  Create an Infernet Wallet.
#   find           Find nodes running the given containers
#   fund           Fund a wallet.
#   health         Health check
#   ids            Get job IDs for this client.
#   info           Get node information.
#   job            Request a job.
#   resources      Get container resources.
#   results        Fetch job results.
#   stream         Request a streamed job.
#   sub            Request a delegated subscription.
```

### Node

#### Node URL

You can pass the node url with every command using `--url`, or you can set it once as an ENV variable:
```bash
export SERVER_URL=http://localhost:4000
```

#### Health
To check the health of the node server, you can use `health`:
```
Usage: infernet-client health [OPTIONS]

  Health check

Options:
  --url TEXT  URL of the server. Can also set SERVER_URL environment variable.
              [required]
```

**Example:**
```bash
infernet-client health
# healthy
```

#### Info
To get node information, such as containers running, pending jobs, and chain details, you can use `info`:
```
Usage: infernet-client info [OPTIONS]

  Get node information.

Options:
  --url TEXT             URL of the server. Can also set SERVER_URL
                         environment variable.  [required]
  -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                         for stdout.
```

**Example:**
```bash
infernet-client info
# {
#   "chain": {
#     "address": "0x...........",
#     "enabled": true
#   },
#   "containers": [
#     {
#       "description": "OpenAI inference + embeddings service",
#       "external": true,
#       "id": "openai-client-inference-0.0.1",
#       "image": "ritualnetwork/llm_inference_service:0.0.1"
#     }
#   ],
#   "pending": {
#     "offchain": 3,
#     "onchain": 1
#   },
#   "version": "0.3.0"
# }
```

#### Resources
To get container resources, such as hardware resources and supported model details, you can use `resources`:
```
Usage: infernet-client resources [OPTIONS]

  Get container resources.

Options:
  --url TEXT             URL of the router. Can also set ROUTER_URL
                         environment variable.  [required]
  -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                         for stdout.
  -n, --node TEXT        Node hostname / IP to check for resources. If not
                         provided, all nodes are returned.
```

**Example:**
```bash
infernet-client resources --node http://localhost:4000
# {
#   "onnx-inference-service": {
#     "compute_capability": [
#       {
#         "cached_models": [],
#         "id": "ml",
#         "models": [],
#         "task": [],
#         "type": "onnx"
#       }
#     ],
#     "hardware_capabilities": [
#       {
#         "capability_id": "base",
#         "cpu_info": {
#           "architecture": "aarch64",
#           "byte_order": "Little Endian",
#           "cores": [],
#           "model": "-",
#           "num_cores": 12,
#           "vendor_id": "Apple"
#         },
#         "disk_info": [
#           {
#             "available": 22042652,
#             "filesystem": "overlay",
#             "mount_point": "/",
#             "size": 122713108,
#             "used": 94404144
#           },
#           {
#             "available": 65536,
#             "filesystem": "tmpfs",
#             "mount_point": "/dev",
#             "size": 65536,
#             "used": 0
#           },
#           {
#             "available": 65536,
#             "filesystem": "shm",
#             "mount_point": "/dev/shm",
#             "size": 65536,
#             "used": 0
#           },
#           {
#             "available": 22042652,
#             "filesystem": "/dev/vda1",
#             "mount_point": "/etc/hosts",
#             "size": 122713108,
#             "used": 94404144
#           },
#           {
#             "available": 4576288,
#             "filesystem": "tmpfs",
#             "mount_point": "/sys/firmware",
#             "size": 4576288,
#             "used": 0
#           }
#         ],
#         "os_info": {
#           "name": "Linux",
#           "version": "#1 SMP PREEMPT Wed Oct 25 16:32:24 UTC 2023"
#         }
#       }
#     ],
#     "service_id": "onnx-inference-service"
#   }
# }
```

#### Model support
To check model support by container, you can use `check-model`:
```
Usage: infernet-client check-model [OPTIONS]

  Check model support.

  If a node is provided, returns support for that node. Otherwise,
  returns all nodes.

Options:
  -m, --model-id TEXT    Model ID to check containers for support.  [required]
  --url TEXT             URL of the router. Can also set ROUTER_URL
                         environment variable.
  -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                         for stdout.
  -n, --node TEXT        Node host / IP to check for resources, otherwise all
                         nodes are returned.
```

**Example:**
```bash
infernet-client check-model -m huggingface/Ritual-Net/iris-classification:iris.onnx
# {
#   "localhost:4000": {
#     "css-inference-service": {
#       "supported": false
#     },
#     "torch-inference-service": {
#       "supported": false
#     }
#   },
#   "localhost:5000": {
#     "onnx-inference-service": {
#       "supported": true
#     },
#     "torch-inference-service": {
#       "supported": false
#     }
#   }
# }
```

#### Request a Job
To request an offchain job, you can use `job`:
```
Usage: infernet-client job [OPTIONS]

  Request a job. Outputs a job ID, or results if sync is enabled.

Options:
  --url TEXT                URL of the server. Can also set SERVER_URL
                            environment variable.  [required]
  -c, --containers TEXT     Comma-separated list of container IDs to request a
                            job from.  [required]
  -i, --input FILENAME      Input file to read the data from. Must be a JSON
                            file. Skip or use '-' for stdin.
  -o, --output FILENAME     Output file to write the result to. Skip or use '-'
                            for stdout.
  --sync                    Whether to wait for the job to complete and return
                            the results.
  --retries INTEGER         Number of 1 second retries to attempt to fetch job
                            results. Defaults to 5.
  --requires-proof BOOLEAN  Whether this job requires proof. Defaults to false.

```

**Example:**
```bash
infernet-client job -c openai-client-inference-0.0.1 -i input.json
# 29dd2f8b-05c3-4b1c-a103-370c04c6850f
```

where `input.json`:
```json
{"model": "text-embedding-3-small", "params": {"endpoint": "embeddings", "input": "Machine learning (ML) is a subset of artificial intelligence (AI) that focuses on creating algorithms and models that enable computers to learn and improve their performance on a specific task."}}
```

To fetch results by `id`, see [Fetch Results](#fetch-results).

Alternatively, you can specify `--sync`, which will wait until the results are available:
```bash
infernet-client job -c openai-client-inference-0.0.1 -i input.json --sync
# [
#  -0.00045939715,
#   0.035724517,
#   0.0002739553,
#   ...,
#   ...,
#   ...,
#   0.032772407,
#   0.014461349,
#   0.049188532
# ]
```

#### Request a streamed Job

To request an offchain job that streams back results, you can use `stream`:
```
Usage: infernet-client stream [OPTIONS]

  Request a streamed job.

Options:
  --url TEXT             URL of the server. Can also set SERVER_URL
                         environment variable.  [required]
  -c, --container TEXT   Container ID to request a streamed job from.
                         [required]
  -i, --input FILENAME   Input file to read the data from. Must be a JSON
                         file. Skip or use '-' for stdin.
  -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                         for stdout.
```

**Example**:
```bash
infernet-client stream -c inference-stream -i input.json
# Job ID: 785c9abd-0e25-4e8c-86e8-be5becba7cfa
# 100 times faster than traditional machine learning

# Deep learning is a subset of machine learning that involves the use of artificial neural networks to analyze and learn from data. It has been gaining popularity in recent years due to its ability to solve complex problems in computer vision, natural language processing, and other areas.

# One of the key advantages of deep learning is its ability to learn and improve on its own. Unlike traditional machine learning, which requires manual feature engineering and optimization, deep learning algorithms can automatically learn and adapt to new data. This makes it much faster and more efficient than traditional machine learning.

# In fact, according to a study by Google researchers, deep learning is up to 100 times faster
```

where `input.json`:
```json
{"prompt": "Deep learning is "}
```

#### Get Job IDs
To get IDs of jobs requested by this client, you can use `ids`:
```
Usage: infernet-client ids [OPTIONS]

  Get job IDs for this client.

Options:
  --url TEXT                      URL of the server. Can also set SERVER_URL
                                  environment variable.  [required]
  -o, --output FILENAME           Output file to write the result to. Skip or
                                  use '-' for stdout.
  --status [pending|completed|all]
                                  Only job IDs with the specified status.
                                  Default is all.
```

**Example:**
```bash
infernet-client ids
# [
#   "09b9d8bb-d752-46aa-ab95-583304827030",
#   "50f098a2-daf7-47a9-9eb8-caf9b7509101",
#   "29dd2f8b-05c3-4b1c-a103-370c04c6850f",
#   "d77215c8-dd25-4843-89c4-788eef9ed324"
# ]

infernet-client ids --status completed
# [
#   "09b9d8bb-d752-46aa-ab95-583304827030",
#   "50f098a2-daf7-47a9-9eb8-caf9b7509101",
#   "29dd2f8b-05c3-4b1c-a103-370c04c6850f",
# ]

infernet-client ids --status pending
# [
#   "d77215c8-dd25-4843-89c4-788eef9ed324"
# ]
```

#### Fetch Results

To fetch results asynchronously by `id`, you can use `results`:
```
Usage: infernet-client results [OPTIONS]

  Fetch job results.

Options:
  --url TEXT             URL of the server. Can also set SERVER_URL
                         environment variable.  [required]
  --id TEXT              Specify a job ID [repeatable].  [required]
  -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                         for stdout.
  --intermediate         Whether to get the intermediate results. Only
                         applicable when multiple containers are used.
```

**Example:**
```bash
infernet-client results --id 29dd2f8b-05c3-4b1c-a103-370c04c6850f --id 09b9d8bb-d752-46aa-ab95-583304827030
# [
#   {
#     "id": "29dd2f8b-05c3-4b1c-a103-370c04c6850f",
#     "result": {
#       "container": "openai-client-inference-0.0.1",
#       "output": [
#         -0.00045939715,
#          0.035724517,
#          0.0002739553,
#         ...,
#         ...,
#         ...,
#         0.032772407,
#         0.014461349,
#         0.049188532
#       ]
#     },
#   "status": "success"
#   },
#   {
#     "id": "09b9d8bb-d752-46aa-ab95-583304827030",
#     "result": {
#       "container": "openai-client-inference-0.0.1",
#       "output": [
#          0.0024995692,
#          -0.001929842,
#          -0.007998622,
#         ...,
#         ...,
#         ...,
#         0.001959762,
#         0.023656772,
#         0.015548443
#       ]
#     },
#   "status": "success"
#   }
# ]
```

#### Request a Delegated Subscription

To request a [Delegated Subscription](https://docs.ritual.net/infernet/sdk/patterns/delegator#creating-off-chain-subscriptions), you can use `sub`:
```
Usage: infernet-client sub [OPTIONS]

  Request a delegated subscription.

  Delegated subscriptions deliver results to a user-defined contract on-chain.

Options:
  --url TEXT            URL of the server. Can also set SERVER_URL environment
                        variable.  [required]
  --rpc_url TEXT        RPC url. Can also set RPC_URL environment variable.
                        [required]
  --address TEXT        Coordinator contract address. Can also set ADDRESS
                        environment variable.  [required]
  --expiry INTEGER      The expiry of the subscription in seconds (UNIX
                        timestamp)  [required]
  --key FILENAME        Path to the private key file. Can also set PRIVATE_KEY
                        environment variable.  [required]
  --params FILENAME     Path to the subscription parameters file.  [required]
  -i, --input FILENAME  Input file to read the data from. Must be a JSON file.
                        Skip or use '-' for stdin.
```

**Example:**
```bash
infernet-client sub --rpc_url http://some-rpc-url.com --address 0x19f...xJ7 --expiry 1713376164 --key key-file.txt \
    --params params.json --input input.json
# Success: Subscription created.
```

where `params.json`:
```js
{
    "owner": "0x00Bd138aBD7....................", // Subscription Owner
    "active_at": 0, // Instantly active
    "period": 3, // 3 seconds between intervals
    "frequency": 2, // Process 2 times
    "redundancy": 2, // 2 nodes respond each time
    "max_gas_price": 1000000000000, // Max gas price in wei
    "max_gas_limit": 3000000, // Max gas limit in wei
    "container_id": "openai-client-inference-0.0.1", // comma-separated list of containers
    "inputs": { // Inputs
        "model": "text-embedding-3-small",
        "params": {
            "endpoint": "embeddings",
            "input": "Machine learning (ML) is a subset of artificial intelligence (AI) that focuses on creating algorithms and models that enable computers to learn and improve their performance on a specific task."
        }
    }
}
```

### Router

#### Router URL

By default, the official Ritual router is used. You can instead pass your own router url with every command using `--url`, or you can set it once as an ENV variable:
```bash
export SERVER_URL=http://localhost:4000
```

#### Containers
To browse all containers currently running across the network, use `containers`:
```
Usage: infernet-client containers [OPTIONS]

  List containers running in the network

Options:
  --url TEXT  URL of the router. Can also set ROUTER_URL environment variable.
```

**Example:**
```bash
infernet-client containers
# [
#   {
#     "id": "hello-world",
#     "count": 100,
#     "description": "Hello World container"
#   },
#   {
#     "id": "ritual-tgi-inference",
#     "count": 3,
#     "description": "Serving meta-llama/Llama-2-7b-chat-hf via TGI"
#   },
# ]
```

#### Find Nodes
To discover nodes running one or more specific containers, use `find`:
```
Usage: infernet-client find [OPTIONS]

  Find nodes running the given containers

Options:
  -c TEXT         Specify a container ID [repeatable].  [required]
  -n INTEGER      The number of nodes to return.
  --skip INTEGER  The offset to start at, for pagination.
  --url TEXT      URL of the router. Can also set ROUTER_URL environment
                  variable.
```

**Examples:**
```bash
infernet-client find -c hello-world
# [
#   "167.86.78.186:4000",
#   "84.54.13.11:4000",
#   "37.27.106.57:4000"
# ]

infernet-client find -c hello-world -n 5 --skip 2
# [
#   "37.27.106.57:4000",
#   "161.97.157.96:4000",
#   "176.98.41.25:4000",
#   "84.46.244.212:4000",
#   "173.212.203.3:4000"
# ]

infernet-client find -c hello-world -c ritual-tgi-inference
# [
#   "37.27.106.57:4000",
#   "161.97.157.96:4000",
# ]

infernet-client find -c goodbye-world
# []
```
