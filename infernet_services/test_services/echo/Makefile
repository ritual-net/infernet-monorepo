DOCKER_ORG := ritualnetwork
SERVICE_NAME := echo
TAG := $(DOCKER_ORG)/$(SERVICE_NAME):latest

build:
	@docker build -t $(TAG) .

run:
	docker run --rm --name $(SERVICE_NAME) -p 3000:3000 $(TAG)
