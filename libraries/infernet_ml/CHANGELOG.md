# Changelog

All notable changes to this project will be documented in this file.

- ##### The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
- ##### This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2024-10-28
- Added `RitualVector` class for unified handling of vectors across various
  libraries as well as encoding/decoding to/from solidity bytes. With support for both
  fixed-point floating point arithmetic as well as IEEE-754 floating point arithmetic.
- Added `RitualRepo` class for a unified standard of dealing with repositories from
  different sources.
- Support for EZKL proof generation through various modules & utility functions.
- Added utility methods & types (in the `spec.py` module) for broadcasting hardware
  capabilities as well as compute capabilities (ZK, LLM Inference, etc.) information
  through a `REST` endpoint.
- New `RitualArtifactManager` class for managing artifacts in a standardized way across
  different storage backends.

## [1.0.0] - 2024-06-06

### Added
- Added tooling for encoding/decoding of vectors to solidity bytes
- Added streaming support to `BaseInferenceWorkflow` with two new methods
  - `stream()`
  - `do_stream()`

### Changed
- Added typed input/output interfaces for
  - `CSSInferenceWorkflow`
  - `TGIClientInferenceWorkflow`
  - `TorchInferenceWorkflow`
  - `ONNXInferenceWorkflow`
  - `HFInferenceClientWorkflow`
  - `model_loader`

### Fixed

## [0.1.0] - 2024-03-21

### Added
- Initial release of Infernet ML.
