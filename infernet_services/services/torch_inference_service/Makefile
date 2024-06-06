DOCKER_ORG := ritualnetwork
SERVICE_NAME := torch_inference_service
TAG := $(DOCKER_ORG)/$(SERVICE_NAME):latest

build:
	@docker build -t $(TAG) --ssh default --build-arg index_url=$(index_url) .

run:
	docker run --rm --env-file .env --name $(SERVICE_NAME) -p 3000:3000 $(TAG)

# You may need to set up a docker builder, to do so run:
# docker buildx create --name mybuilder --bootstrap --use
# refer to https://docs.docker.com/build/building/multi-platform/#building-multi-platform-images for more info
build-multiplatform:
	docker buildx build --platform linux/amd64,linux/arm64 \
	    --build-arg index_url=$(index_url) -t $(TAG) --push .
