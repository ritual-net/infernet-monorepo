specs:
	@python libraries/infernet_ml/src/infernet_ml/utils/spec.py

DOCKER := docker
ifeq ($(shell uname -s),Darwin)
    DOCKER := docker
    PLATFORM := linux/arm64
else
    DOCKER := docker
    PLATFORM := linux/amd64
endif
