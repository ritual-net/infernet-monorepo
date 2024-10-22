# Infernet ML

### What is Infernet ML?

Ritual provides easy-to-use abstractions for users to create AI/ML workflows that can be
deployed on Infernet nodes.
The [`infernet-ml`](https://github.com/ritual-net/infernet-ml) library is a Python SDK
that provides a set of tools and extendable classes for creating and
deploying machine learning workflows. It is designed to be easy to use, and provides a
consistent interface for data pre-processing, inference, and post-processing of data.

### Batteries Included

We provide a set of pre-built workflows for common use-cases. We have workflows for
running ONNX models, Torch models,
any Huggingface model
via [Huggingface inference client](https://huggingface.co/docs/huggingface_hub/en/package_reference/inference_client)
and even for closed-source models such as OpenAI's GPT-4.

### Getting Started

Head over to the [next section](./quickstart.md) for installation and a quick
walkthrough of
the ML workflows.

### What's new in `infernet-ml 2.0`?

The following new features have been added in `infernet-ml 2.0`:

1. Addition of [`ModelManager`](./reference/infernet_ml/utils/model_manager/?h=modelmana#infernet_ml.utils.model_manager.ModelManager) class
   for uploading/downloading models to/from various storage layers. Currently supported: `huggingface`, `arweave`. For a tutorial on this, head
   to the [Managing Models](./models.md) page.
2. [`ArtifactManager`](./reference/infernet_ml/resource/artifact_manager/) is a base class for managing various kinds of artifacts. Used for both ML models as well as EZKL artifacts,
   [`ArtifactManager`](./reference/infernet_ml/resource/artifact_manager/) is an easy-to-use abstraction for handling various compute artifacts.
3. [`RitualVector`](./reference/infernet_ml/utils/codec/vector/?h=ritualvec#infernet_ml.utils.codec.vector.RitualVector) is an easy-to-use class to represent vectors on-chain.
   It supports both [fixed-point](https://en.wikipedia.org/wiki/Fixed-point_arithmetic), and [floating-point](https://en.wikipedia.org/wiki/IEEE_754#Design_rationale) representations.
