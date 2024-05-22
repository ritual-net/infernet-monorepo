from typing import Any, cast

from eth_abi import decode, encode  # type: ignore
from flask import Flask, request
from pydantic import ValidationError

from infernet_ml.utils.service_models import InfernetInput, InfernetInputSource


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
            case InfernetInput(source=InfernetInputSource.OFFCHAIN, data=data):
                print(f"received Offchain Request: {data}")
                hex_input = cast(str, data["input"])
            case InfernetInput(source=InfernetInputSource.CHAIN, data=data):
                print(f"received On-chain Request: {data}")
                hex_input = cast(str, data)
            case _:
                raise ValidationError(
                    "Invalid InferentInput type: expected mapping for offchain "
                    "input type"
                )

        (input,) = decode(["uint8"], bytes.fromhex(hex_input), strict=False)
        print(f"decoded data: {input}")

        return {
            "raw_input": hex_input,
            "processed_input": "",
            "raw_output": encode(["uint8"], [input]).hex(),
            "processed_output": "",
            "proof": "",
        }

    return app


if __name__ == "__main__":
    create_app().run(port=3000, debug=True)
