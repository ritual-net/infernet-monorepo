DOCKER_ORG := ritualnetwork
service_name := echo
TAG := $(DOCKER_ORG)/$(service_name):latest

build:
	@docker build -t $(TAG) --build-arg index_url=$(index_url) .

run:
	docker run --rm --name $(service_name) -p 3000:3000 $(TAG)
