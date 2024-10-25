FROM ghcr.io/foundry-rs/foundry:nightly-25598999a2b33ac6ccfa35c347f3c98aba8e0061@sha256:5932c7005b4b4e5442587ba891b8a156f37585f2bef72ea13e246533516dc8cf

WORKDIR /app

COPY  infernet_deployed.json .

ENTRYPOINT [ "anvil"]
CMD [ "--host", "0.0.0.0", "--port", "3000", "--load-state", "infernet_deployed.json"]