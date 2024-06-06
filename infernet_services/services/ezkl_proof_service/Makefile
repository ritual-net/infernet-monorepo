DOCKER_ORG := ritualnetwork
SERVICE_NAME := ezkl_proof_service
TAG := $(DOCKER_ORG)/$(SERVICE_NAME):latest
index_url := https://_token:ya29.c.c0AY_VpZhtr3CzUWoV8LxulcaZcLp7VNuRUk32MMuF-7wEAY7cT6UaKlr3KqDqxiZuQJex9rWsq15RYQ8DaUbwoOQtqPBLXeyg-4tg2DOlAYQrfaeC2rfwrej8O8KQHcxRp4TTaVNdvs6gQGPpewtFmxu_4KOXxZRVNhVyiPuy8xRBnko7R6xEqvZbcScHJNMK8kCIbTP1zriF2iJ4jCnqYXRyVdqJudwPoPwYStfWA4ap7ON9gYYhXQQ8n4_z3kX9-RlyJwZ0m9R_RdJvMYVpUVKoX1Kbajul6QCdmNW5Eu8rYnxmjz-22swGclr4z1EK1MKGmuuy60gn03Aa2YqQeLIw4-SN2tIze9ds8qvK8GlDBUDI-h44EukEPzqp7jCY2hm9H397PSaYxkayalw8lqZOVqqRrWI82Wr_wwO7-QogpY_ZBVbWci7mpYfgiklMIhi4fnOMiFfRVt6y75FVgWOrVpaFMg1WRvdOF83-s56vrRniihBbax3Fq8msvBYrrVqBMgY2Bbu2iRv78dt6-WOxWqbsMxrrRujkycjOVRnp1aFJupwSJ29c6R-hSjtBsQ04vwmt_0twiJd2BFZlz6Q9xYJlQlvf_tY7JXXVOjOgJQbiZ8symy9kkqz5g9Ss9vVB8lgV2a0IkM6BjWo35buUl3i-JkJgor3M6RbqpOWBb8VBIdeOQWJ2Y8Wy9vJpaf1ybVsntk-ldrZF6UOZXI02mIMwkbWdk3M1gf79wa_8i6faMzcOzs4i8lmeWtRS7Qs0z8JIb41jjjQu9Mqpur8d-VaxFzwhZbreuW0Y73JXojsmipf_if5tO67wVtnS5kYBjcq7R_InQz6IMp6Q366Yf-5zqjXV2fU0B-l0I0yQSYMddcrYVtVj7jU_h1xvbk0nsd1nYqnI8nde1dd1xSkl3zUfxsqbxpZkOJiuB09ekylymqg1O45Booowll0xvBxiIn73aVBhJmaSc1BF1vS3lWdgniuS8dawk6o_q3F-12grorXWlvO@northamerica-northeast2-python.pkg.dev/private-pypi-418615/ritual-pypi/simple

build: # force AMD because ezkl only supports musllinux for AARCH64, which doesnt support Torch.
	@docker build -t $(TAG) --platform linux/amd64 --ssh default --build-arg index_url=$(index_url) .

run:
	docker run --rm --env-file .env --name $(SERVICE_NAME) -p 3000:3000 $(TAG)


# You may need to set up a docker builder, to do so run:
# docker buildx create --name mybuilder --bootstrap --use
# refer to https://docs.docker.com/build/building/multi-platform/#building-multi-platform-images for more info
build-multiplatform:
	docker buildx build --platform linux/amd64,linux/arm64 \
	    --build-arg index_url=$(index_url) -t $(TAG) --push .
