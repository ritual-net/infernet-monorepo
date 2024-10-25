from typing import Any, Dict, cast

from eth_abi.abi import decode, encode
from flask import Flask, request
from infernet_ml.services.types import InfernetInput, JobLocation
from pydantic import ValidationError


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index() -> dict[str, str]:
        return {"message": "Echo Service!"}

    @app.route("/service_output", methods=["POST"])
    def inference() -> dict[str, Any]:
        body: dict[str, Any] = cast(dict[str, Any], request.json)
        inf_input = InfernetInput(**body)
        match inf_input:
            case InfernetInput(source=JobLocation.OFFCHAIN, data=data):
                print(f"received Offchain Request: {data}")
                hex_input = cast(str, cast(Dict[str, Any], data)["input"])
            case InfernetInput(source=JobLocation.ONCHAIN, data=data):
                print(f"received On-chain Request: {data}")
                hex_input = cast(str, data)
            case _:
                raise ValidationError(
                    "Invalid InferentInput type: expected mapping for offchain "
                    "input type"
                )

        (input, proof) = decode(
            ["string", "string"], bytes.fromhex(hex_input), strict=False
        )

        match inf_input:
            case InfernetInput(requires_proof=True):
                proof = encode(["string"], [proof]).hex()
            case _:
                proof = ""

        return {
            "raw_input": hex_input,
            "processed_input": "",
            "raw_output": encode(["string"], [input]).hex(),
            "processed_output": "",
            "proof": proof,
        }

    return app


if __name__ == "__main__":
    create_app().run(port=3000, debug=True)
