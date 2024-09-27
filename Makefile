include scripts/setup.mk
include scripts/utils.mk
include scripts/docs.mk
include scripts/gcp.mk
include scripts/pypi.mk
include scripts/libraries.mk
include scripts/rust_bindings.mk
include infernet_services/services.mk

SHELL := /bin/bash

# suppress "entering directory" messages
MAKEFLAGS += --no-print-directory

clean:
	rm -rf dist
