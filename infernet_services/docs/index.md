# Infernet Services 

Inference services are a collection of docker containerized python flask apps that utilize infernet_ml workflows to process a variety of inference requests from infernet nodes. The source and destination of these inference requests can be both offchain and onchain, and some also support streaming for offchain destinations. These services are designed to be scalable, efficient, and easy to integrate with various machine learning models and data sources.

The following workflows are currently supported as infernet services:

- CSS (Closed-Source Software, models like OpenAI) **supports streaming**
- ONNX
- TGI Client **supports streaming**
- Torch
