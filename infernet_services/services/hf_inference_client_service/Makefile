DOCKER_ORG := ritualnetwork
SERVICE_NAME := hf_inference_client_service
TAG := $(DOCKER_ORG)/$(SERVICE_NAME):latest

build:
	@docker build -t $(TAG) --ssh default --build-arg index_url=$(index_url) .

run:
	docker run --rm --name $(SERVICE_NAME) -p 3000:3000 $(TAG)
