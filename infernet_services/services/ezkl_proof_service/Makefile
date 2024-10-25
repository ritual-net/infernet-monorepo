DOCKER_ORG := ritualnetwork
BASE_NAME := ezkl_proof_base
service_name := ezkl_proof_service_internal

TAG := $(DOCKER_ORG)/$(service_name):1.0.0
BASE_TAG := $(DOCKER_ORG)/$(BASE_NAME):1.0.0

VANILLA_BUILD = $(DOCKER) build
BUILDX_BUILD = $(DOCKER) buildx build

include ../../../scripts/utils.mk

build-base:
	$(VANILLA_BUILD) -t $(BASE_TAG) --platform linux/amd64 --build-arg index_url=$(index_url) -f base.Dockerfile --load .

build: # force AMD because ezkl only supports musllinux for AARCH64, which doesnt support Torch.
	$(VANILLA_BUILD) -t $(TAG) --platform linux/amd64 --build-arg index_url=$(index_url) --load .

run:
	docker run --rm --env-file .env --name $(service_name) -p 3000:3000 $(TAG)

push:
	docker push $(TAG)

# You may need to set up a docker builder, to do so run:
# docker buildx create --name mybuilder --bootstrap --use
# refer to https://docs.docker.com/build/building/multi-platform/#building-multi-platform-images for more info
build-multiplatform:
	docker buildx build --platform linux/amd64,linux/arm64 --build-arg index_url=$(index_url) -t $(TAG) --push .
