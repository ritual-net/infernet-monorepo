FROM ghcr.io/foundry-rs/foundry:latest@sha256:b825b406691c60e510c83986efa9282e95e770800e1553a98b816c0ecff0485e

WORKDIR /app

COPY  infernet_deployed.json .

ENTRYPOINT [ "anvil"]
CMD [ "--host", "0.0.0.0", "--port", "3000", "--load-state", "infernet_deployed.json"]
