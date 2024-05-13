from typing import Any, cast

from eth_abi import decode, encode  # type: ignore
from flask import Flask, request


def create_app() -> Flask:
    app = Flask(__name__)

    @app.route("/")
    def index() -> dict[str, str]:
        return {"message": "Echo Service!"}

    @app.route("/service_output", methods=["POST"])
    def inference() -> dict[str, Any]:
        body: dict[str, Any] = cast(dict[str, Any], request.json)
        (input,) = decode(["uint8"], bytes.fromhex(cast(str, body.get("data"))))
        print(f"input is: {input}")

        return {
            "raw_input": encode(["uint8"], [input]).hex(),
            "processed_input": "",
            "raw_output": encode(["uint8"], [input]).hex(),
            "processed_output": "",
            "proof": "",
        }

    return app


if __name__ == "__main__":
    create_app().run(port=3000)
