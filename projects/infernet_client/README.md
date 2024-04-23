# Infernet Client

Welcome to the Infernet Client, a lightweight Python library and CLI tool that streamlines interaction with the [REST server](https://docs.ritual.net/infernet/node/api) of the [Infernet Node](https://docs.ritual.net/infernet/node/introduction). The Infernet Node provides robust computational capabilities through a well-defined API. This client aims to provide developers with a simple, efficient way to integrate and automate tasks using the Infernet Node.

## Features

- **Simple**: Streamlined methods for interacting with the Infernet Node API.
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
#   health   Health check
#   ids      Get job IDs for this client.
#   info     Get node information.
#   job      Request a job.
#   results  Fetch job results.
#   stream   Request a streamed job.
#   sub      Request a delegated subscription.
```

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

#### Request a Job
To request an offchain job, you can use `job`:
```
Usage: infernet-client job [OPTIONS]

  Request a job. Outputs a job ID, or results if sync is enabled.

Options:
  --url TEXT             URL of the server. Can also set SERVER_URL
                         environment variable.  [required]
  -c, --containers TEXT  Comma-separated list of container IDs to request a
                         job from.  [required]
  -i, --input FILENAME   Input file to read the data from. Must be a JSON
                         file. Skip or use '-' for stdin.
  -o, --output FILENAME  Output file to write the result to. Skip or use '-'
                         for stdout.
  --sync                 Whether to wait for the job to complete and return
                         the results.
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
