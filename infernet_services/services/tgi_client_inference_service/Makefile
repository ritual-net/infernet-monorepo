DOCKER_ORG := ritualnetwork
service_name := tgi_client_inference_service
TAG := $(DOCKER_ORG)/$(service_name):2.0.0

build:
	@docker build -t $(TAG) --build-arg index_url=$(index_url) .

run:
	docker run --rm --env-file .env --name $(service_name) -p 3000:3000 $(TAG)

# You may need to set up a docker builder, to do so run:
# docker buildx create --name mybuilder --bootstrap --use
# refer to https://docs.docker.com/build/building/multi-platform/#building-multi-platform-images for more info
build-multiplatform:
	docker buildx build --platform linux/amd64,linux/arm64 \
	    --build-arg index_url=$(index_url) -t $(TAG) --push .
