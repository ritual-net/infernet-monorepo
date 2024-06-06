# Changelog

All notable changes to this project will be documented in this file.

- ##### The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
- ##### This project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
