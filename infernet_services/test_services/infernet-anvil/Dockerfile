FROM ghcr.io/foundry-rs/foundry:latest

WORKDIR /app

COPY  infernet_deployed.json .

ENTRYPOINT [ "anvil"]
CMD [ "--host", "0.0.0.0", "--port", "3000", "--load-state", "infernet_deployed.json"]