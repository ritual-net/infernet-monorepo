from __future__ import annotations

from pathlib import Path
from typing import Any, List, Optional

from eth_abi.abi import decode, encode
from pydantic import BaseModel

from infernet_ml.utils.codec.vector import ArithmeticType, RitualVector
from infernet_ml.utils.specs.ml_model_id import MlModelId
from infernet_ml.workflows.inference.onnx_inference_workflow import ONNXInferenceInput

ONNX_SERVICE_PREFIX = "ONNX"


class ONNXServiceConfig(BaseModel):
    DEFAULT_MODEL_ID: Optional[str] = None
    CACHE_DIR: Optional[str] = f'{Path("~/.cache/ritual").expanduser().absolute()}'

    def to_env_dict(self) -> dict[str, str | None]:
        return {
            "ONNX_DEFAULT_MODEL_ID": self.DEFAULT_MODEL_ID,
            "ONNX_CACHE_DIR": self.CACHE_DIR,
        }


class ONNXInferenceRequest(BaseModel):
    model_id: Optional[str] = None
    inputs: dict[str, RitualVector]
    output_arithmetic: Optional[ArithmeticType] = None
    output_num_decimals: Optional[int] = None

    def to_web3(
        self, arithmetic: ArithmeticType = ArithmeticType.ieee, num_decimals: int = 18
    ) -> bytes:
        types = ["bytes", "bytes"]

        values: List[Any] = [
            MlModelId.from_unique_id(self.model_id).to_web3 if self.model_id else b"",
            list(self.inputs.values())[0].to_web3(arithmetic, num_decimals),
        ]

        if self.output_arithmetic:
            types.append("uint8")
            values.append(self.output_arithmetic.to_int_enum())
        if self.output_num_decimals:
            types.append("uint8")
            values.append(self.output_num_decimals)

        return encode(types, values)

    @classmethod
    def from_web3(cls, hex_input: str) -> ONNXInferenceRequest:
        (
            model_id,
            vector_hex,
        ) = decode(
            ["bytes", "bytes"],
            bytes.fromhex(hex_input),
        )
        return cls(
            model_id=MlModelId.from_web3(model_id).unique_id if model_id else None,
            inputs={"input": RitualVector.from_web3(vector_hex)},
        )

    @property
    def workflow_input(self) -> ONNXInferenceInput:
        return ONNXInferenceInput(
            model_id=self.model_id,
            inputs=self.inputs,
        )
