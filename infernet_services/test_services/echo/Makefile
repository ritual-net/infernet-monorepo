DOCKER_ORG := ritualnetwork
SERVICE_NAME := echo-test-service
TAG := $(DOCKER_ORG)/$(SERVICE_NAME):latest

build:
	@docker build -t $(TAG) --ssh default .

run:
	docker run --rm --name $(SERVICE_NAME) -p 3000:3000 $(TAG)
