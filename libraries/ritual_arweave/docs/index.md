# Ritual Arweave Documentation
## Overview
Ritual Arweave is a Python library and CLI tool designed to facilitate the uploading and downloading of data to and from the Arweave network. This library supports both individual file operations and repository-level operations, making it versatile for various use cases, including model storage and retrieval in machine learning projects.

## Key Features
- Upload and Download Individual Files: Easily manage single files on the Arweave network.
- Upload and Download Repositories: Handle entire directories containing multiple files, ideal for managing grouped artifacts.
- CLI Support: Use command-line interface for streamlined operations without writing additional code.

## Main Components
- File Manager (file_manager.py): Handles the uploading and downloading of individual files.
- Repository Manager (repo_manager.py): Manages the uploading and downloading of repositories, including handling manifest files and version mappings.