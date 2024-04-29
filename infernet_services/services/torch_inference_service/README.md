# torch ml inference service

A simple service that serves models via the corresponding BaseMLInferenceWorflow.


# End points
**/service_output** - main end point that is used to make inference requests.

Infernet services are expected to implement a end point at `/service_output` that takes a json payload that conforms to the InfernetInput model:

```python
HexStr = Annotated[
    str, StringConstraints(strip_whitespace=True, pattern="^[a-fA-F0-9]+$")
]

class InfernetInputSource(IntEnum):
    CHAIN = 0
    OFFCHAIN = 1

class InfernetInput(BaseModel):
    source: InfernetInputSource
    data: Union[HexStr, dict[str, Any]]
```
This is meant to let services handle both CHAIN and OFFCHAIN data. For more info, see Infernet Node documentation.

Currently, the torch ml inference service only supports OFFCHAIN data. The data field therefore expects json input. Depending on the Inference Workflow, the schema of the json may vary.

For TorchInferenceWorflow, we expect a json dict that confirms to:

```python
{
    "dtype":  "float" | "double" |  "cfloat" | "cdouble" | "half": | "bfloat16" |  "uint8" | "int8" | "short" | "int" | "long" | "bool",
    "values": [...] # matrix shape depends on model
}
```
(The dict may have additional keys which will be ignored)

# Environment Arguments


**CLASSIC_INF_WORKFLOW_CLASS** - fully qualified name of workflow class. For example, "infernet_ml.workflows.inference.llm_inference_workflow.TGIClientInferenceWorkflow" (str is expected)
**CLASSIC_INF_WORKFLOW_POSITIONAL_ARGS** - any positional args required to instantiate the classic inference workflow (List is expected)
**CLASSIC_INF_WORKFLOW_KW_ARGS** - any keyword arguments required to instantiate the classic inference workflow. (Dict is expected)
**HUGGING_FACE_HUB_TOKEN** (optional) - if any files needed from huggingface hub

NOTE: Additional environment arguments may be required depending on the workflow class implementation. See corresponding documentation for details.

For example, if you are using the TorchInferenceWorkflow:

    the model filename (defaulted to model.torch) to download from in HF can be sepcified via TORCH_MODEL_FILE_NAME, and jit torchscipt  model loading can be turned on via USE_JIT (defaulted to False).

    By default, uses hugging face to download the model file, which requires HUGGING_FACE_HUB_TOKEN to be set in the env vars to access private models. if the USE_ARWEAVE env var is set to true, will attempt to download models via Arweave, reading env var ALLOWED_ARWEAVE_OWNERS as well.


# Launching

The easiest way to launch this service is to run from the dockerhub image, which hosts the service via hypercorn:

```bash
# start containers
sudo docker run --name=classic_inf_service -p 4998:3000 --env-file classic_inference_service.env "ritualnetwork/infernet-classic-inference:0.0.4" --bind=0.0.0.0:3000 --workers=2
```

This starts the service via hypercorn with 2 workers at port 4998, reading in environment variables from classic_inference_service.env.

if you have custom workflow dependencies, you should create your own image using the provided one as a base.

Example curl if you are using TorchInferenceWorkflow:
```bash
curl -X POST http://localhost:4998/service_output \
     -H "Content-Type: application/json" \
     -d '{"source": 1, "data":{"bot":"\ud83d\ude0c\nIm not interested in buying your shares, but Im excited","dtype":"double","values":[[0.40234944224357605,0.1991768330335617,0.3301149904727936,0.16184736788272858,0.7940273880958557,0.2978357970714569,0.4644451439380646,-0.07875507324934006,-0.5264527797698975,-0.0305143054574728,0.19991940259933472,-0.18741925060749054,-0.36449891328811646,0.22513322532176971,-2.347233772277832,-0.334255188703537,-0.13411228358745575,0.49123191833496094,0.014900433830916882,0.24287664890289307,0.3498936891555786,-0.5323450565338135,-0.4285130798816681,-0.06870583444833755,0.2772831618785858,0.5927870273590088,0.28189918398857117,-3.705282211303711,-0.06679823994636536,0.13001947104930878,0.05250409618020058,0.3225162625312805,0.2387755662202835,-0.4814269542694092,-0.5147349834442139,0.9515089392662048,-0.2831220328807831,-0.3751475214958191,-0.21504633128643036,-0.37807127833366394,-0.6022977828979492,-1.7188574075698853,0.15128083527088165,-0.5734276175498962,0.8299591541290283,-0.34354695677757263,-0.6261964440345764,0.07565336674451828,-0.08066360652446747,-0.15466998517513275,-0.7615634202957153,-0.04209704324603081,0.8875067830085754,0.5063599944114685,-0.599464476108551,-0.33804187178611755,-0.4338133931159973,-1.8838119506835938,0.06673427671194077,0.5949566960334778,-0.8291200995445251,-0.2526260018348694,-0.48558521270751953,0.2823924422264099,0.24268318712711334,-0.05079847201704979,-5.335397720336914,0.2539847195148468,0.00097266974626109]]}}'

```

If local deployment is desired, ensure your python path includes the src directory, either by installing the ml project or by manually setting PYTHONPATH, and run the quart dev server:

```bash
pip install -r requirements.txt
export PYTHONPATH=src
QUART_APP=torch_inference_service:create_app quart -e torch_inference_service.env run --reload
```
