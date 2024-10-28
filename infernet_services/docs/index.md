# Infernet Services

Inference services are a collection
of [Infernet-compatible](https://docs.ritual.net/infernet/node/containers#infernet-compatible-containers)
containers that can be used to perform a variety of inference requests with
the [Infernet Node](https://docs.ritual.net/infernet/node/introduction).

Each service is a docker containerized python quart app that
utilizes [`infernet-ml`](https://infernet-ml.docs.ritual.net/)'s
workflows to perform different flavors of ML inference. The source and destination of
the requests to these services can be either `offchain` or `onchain`, and some also
support streaming for offchain destinations. These services are designed to be scalable,
efficient, and easy to integrate with various machine learning models and data sources.

The following workflows are currently supported as Infernet services:

| Service                                              | Description                                | Supports streaming |
|------------------------------------------------------|--------------------------------------------|--------------------|
| [CSS](reference/css_inference_service)               | Closed-Source Software, models like OpenAI | Yes                |
| [HF Client](reference/hf_inference_client_service)   | HuggingFace Inference Client               | No                 |
| [ONNX](reference/onnx_inference_service)             | Open Neural Network Exchange               | No                 |
| [TGI Client](reference/tgi_client_inference_service) | Text Generation Inference Client           | Yes                |
| [Torch](reference/torch_inference_service)           | PyTorch Inference                          | No                 |
| [EZKL](reference/ezkl_proof_service)                 | EZKL Proof Generation                      | No                 |
