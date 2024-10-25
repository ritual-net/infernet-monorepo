# EZKL proof service

[EZKL](https://github.com/zkonduit/ezkl) is an engine for doing inference for deep
learning models and other computational graphs in a zk-snark (ZKML).

This service allows you to create proof requests for EZKL models. Using `infernet-ml`,
you can also verify the correctness of the proof.

## Infernet Configuration

The service can be configured as part of the overall Infernet configuration
in `config.json`.

```json
{
    "log_path": "infernet_node.log",
    //...... contents abbreviated
    "containers": [
        {
            "id": "ezkl_proof_service",
            "image": "ritualnetwork/ezkl_proof_service:latest",
            "external": true,
            "port": "3000",
            "allowed_delegate_addresses": [],
            "allowed_addresses": [],
            "allowed_ips": [],
            "command": "--bind=0.0.0.0:3000 --workers=2",
            "env": {
                "HF_TOKEN": "your-huggingface-token",
                "ARTIFACT_DIRECTORY": "~/.cache/ritual"
            }
        }
    ]
}
```

## Environment Variables

### HF_TOKEN

- **Description**: The HuggingFace API token to use for downloading models.
  No need to set this variable if your ezkl artifacts (model file, compiled circuit, etc.)
  are public. Use this if your artifacts are in a private Huggingface repo.
- **Default**: None
- **Example**: get one from [Huggingface](https://huggingface.co/).

### ARTIFACT_DIRECTORY

- **Description**: The local directory to store huggingface artifacts in.
- **Default**: None
- **Example**: `"~/.cache/ritual"`

## Artifacts

Refer to the [EZKL artifact generation]() documentation for a tutorial on how to create your own ezkl artifacts.

## Usage

This service only supports off-chain requests for the time-being. On-chain request support will be added in the
future.

### Offchain (web2) Request

**Please note**: The examples below assume that you have an Infernet Node running locally on port `4000`.

=== "Python"
    You can make a proof request like so:

    ```python

    SERVICE_NAME = "ezkl_proof_service"

    client = NodeClient("http://127.0.0.1:4000")

    # Define inputs
    proof_req = EZKLGenerateProofRequest(
        repo_id=repo_id,
        witness_data=WitnessInputData.from_numpy(
          input_vector=numpy.array([1.0380048, 0.5586108, 1.1037828, 1.712096])
        ),
    )

    ezkl_request = InfernetInput(
        source=JobLocation.OFFCHAIN,
        destination=JobLocation.OFFCHAIN,
        data=proof_req.model_dump(),
    )

    # Define request
    job_request = JobRequest(
        containers=[SERVICE_NAME],
        data=ezkl_request.model_dump()
    )

    # Request the job
    job_id = await client.request_job(job_request)

    # Fetch results
    result = (await client.get_job_result_sync(job_id))["result"]

    # Get the proof
    proof = result.get("ezkl_proof")

    # Get the output
    output = result.get("output")

    ```

    With this, you can verify the proof like so:

    ```python
    from infernet_ml.zk.ezkl.ezkl_utils import verify_proof_from_repo

    r = await verify_proof_from_repo(result.get("ezkl_proof"), repo_id=repo_id)
    ```

=== "CLI"

    ```bash
    # Note that the sync flag is optional and will wait for the job to complete.
    # If you do not pass the sync flag, the job will be submitted and you will receive a job id, which you can use to get the result later.
    infernet-client job -c ezkl_proof_service -i input.json --sync
    ```

    where `input.json` looks like this:

    ```json
    {
        "repo_id": "huggingface/Ritual-Net/ezkl_linreg_10_features",
        "witness_data": {
            "input_data": {
                "dtype": 1,
                "shape": [
                    1,
                    10
                ],
                "values": [
                    0.06637126207351685,
                    0.09468276053667068,
                    0.974238395690918,
                    0.737287163734436,
                    0.8200138211250305,
                    0.4537636339664459,
                    0.0689813494682312,
                    0.46179142594337463,
                    0.21672245860099792,
                    0.807859480381012,
                ]
            },
            "output_data": null
        },
        "vk_address": null
    }
    ```

=== "cURL"

    ```bash
    curl -X POST http://127.0.0.1:4000/api/jobs \
        -H "Content-Type: application/json" \
        -d '{
            "containers": ["ezkl_proof_service"],
            "data": {
                "source": "OFFCHAIN",
                "destination": "OFFCHAIN",
                "data": {
                    "repo_id": "huggingface/Ritual-Net/ezkl_linreg_10_features",
                    "witness_data": {
                        "input_data": {
                            "dtype": 1,
                            "shape": [
                                1,
                                10
                            ],
                            "values": [
                                0.06637126207351685,
                                0.09468276053667068,
                                0.974238395690918,
                                0.737287163734436,
                                0.8200138211250305,
                                0.4537636339664459,
                                0.0689813494682312,
                                0.46179142594337463,
                                0.21672245860099792,
                                0.807859480381012,
                            ]
                        },
                        "output_data": null
                    },
                    "vk_address": null
                }
            }
        }'
    ```
