# Changelog

All notable changes to this project will be documented in this file.

- ##### The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
- ##### This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-10-28

### Changed

- All services now use `infernet-ml >= 2.0.0`
 
### Added
- `ezkl_proof_service`

## [1.0.0] - 2024-06-06

### Added

- Initial release of Infernet Services.
- Created generalized-reusable services for 5 different types of workflows:
  - `css_inference_service`
  - `onnx_inference_service`
  - `torch_inference_service`
  - `tgi_inference_service`
  - `hf_client_inference_service`
