# Infernet Services

Inference services are a collection of docker containerized python flask apps that utilize [infernet_ml](../infernet_ml/) workflows to process a variety of inference requests from infernet nodes. The source and destination of these inference requests can be both offchain and onchain, and some also support streaming for offchain destinations. These services are designed to be scalable, efficient, and easy to integrate with various machine learning models and data sources.

The following workflows are currently supported as infernet services:

| Service | Description | Supports streaming |
|---------|-------------|--------------------|
| [CSS](reference/css_inference_service) | Closed-Source Software, models like OpenAI | Yes |
| [HF Client](reference/hf_inference_client_service) | HuggingFace Inference Client | No |
| [ONNX](reference/onnx_inference_service) | Open Neural Network Exchange | No |
| [TGI Client](reference/tgi_client_inference_service) | Text Generation Inference Client | Yes |
| [Torch](reference/torch_inference_service) | PyTorch Inference  | No |
