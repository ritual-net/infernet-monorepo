from __future__ import annotations

import json
import logging
import os
import platform
import shlex
import subprocess
from enum import StrEnum
from typing import Annotated, Any, Callable, List, Literal, Optional, Union
from xml.etree.ElementTree import Element

from huggingface_hub import HfApi  # type: ignore
from pydantic import BaseModel, Discriminator, Tag
from quart import Quart, request

from infernet_ml.resource.artifact_manager import BroadcastedArtifact, CachedArtifact
from infernet_ml.utils.css_mux import CSSProvider
from infernet_ml.utils.specs.ml_model_id import MlModelId
from infernet_ml.utils.specs.ml_type import MLType


def null_query_handler() -> Callable[[str], dict[str, bool]]:
    """
    Generates a handler for checking if a model is supported by the service.
    This handler always returns False, and is used for services that do not
    advertise their supported model(s).

    Args:
        model_id (str): The model id to check if it is supported. This is ignored.

    Returns:
        handler (Callable[[str], dict[str, bool]]): The handler function to check if
            a model is supported by the service.
    """

    def handler(model_id: str) -> dict[str, bool]:
        return {"supported": False}

    return handler


def simple_query_handler(
    supported_models: List[str],
) -> Callable[[str], dict[str, bool]]:
    """
    Generates a handler for checking if a model is supported by the service. This
    handler checks if the model id is in the list of supported models.

    Args:
        supported_models (List[str]): The list of supported models

    Returns:
        handler (Callable[[str], dict[str, bool]]): The handler function to check if
            a model is supported by the service.
    """

    def handler(model_id: str) -> dict[str, bool]:
        return {"supported": model_id in supported_models}

    return handler


def postfix_query_handler(postfix: str) -> Callable[[str], dict[str, bool]]:
    """
    Generates a handler for checking if a model has a specific postfix. The onnx & torch
    service use this to quickly broadcast if a model is supported by the service.

    Args:
        postfix (str): The postfix to check for in the model files

    Returns:
        handler (Callable[[str], dict[str, bool]]): The handler function to check if
            a model is supported by the service.
    """

    def handler(model_id: str) -> dict[str, bool]:
        model = MlModelId.from_unique_id(model_id)
        if model.files[0].endswith(postfix):
            return {"supported": True}
        else:
            return {"supported": False}

    return handler


def hf_api_query_handler(
    any_tags: List[str] = [], all_tags: List[str] = [], token: Optional[str] = None
) -> Callable[[str], dict[str, bool]]:
    """
    Generates a handler for checking if a model is available on HuggingFace. Includes
    private models if the provided token is valid and has access to them.

    Args:
        any_tags (List[str]): List of tags to filter the models by. At least one of the
            tags must be present in the model's tags.
        all_tags (List[str]): List of tags to filter the models by. All of the tags must
            be present in the model's tags.
        token (Optional[str]): HuggingFace API token. Defaults to None.

    Returns:
        handler (Callable[[str], dict[str, bool]]): The handler function to check if
            a model is supported by the HF API.
    """

    def handler(model_id: str) -> dict[str, bool]:
        try:
            info = HfApi(token=token).model_info(model_id)
            supported = True
            if all_tags:
                # Check if all tags are present in the model's tags
                supported = all([tag in info.tags for tag in all_tags])
            if any_tags:
                # Check if at least one tag is present in the model's tags
                supported = supported and any([tag in info.tags for tag in any_tags])
            return {"supported": supported}
        except Exception:
            # model_info will raise an exception if the model is not found
            return {"supported": False}

    return handler


def ritual_service_specs(
    app: Quart,
    resource_generator: Callable[[], dict[str, Any]],
    model_query_handler: Callable[[str], dict[str, bool]],
) -> None:
    """
    Generates the service resources endpoint for Ritual's services. This endpoint is used
    to broadcast the capabilities of the service for routers & indexing services.

    Args:
        app (Quart): The Quart application
        resource_generator (Callable[[], dict[str, Any]]): The function to generate
            the resources of the service
        model_query_handler (Callable[[str], dict[str, bool]]): The function to
            generate the model query handler

    Returns:
        None
    """

    @app.route("/service-resources")
    async def service_resources_endpoint() -> Any:
        model_id = request.args.get("model_id", "")
        if not model_id:
            return resource_generator()
        try:
            return model_query_handler(model_id)
        except Exception as e:
            return {"supported": False, "error": str(e)}


log = logging.getLogger(__name__)


class ComputeId(StrEnum):
    """
    ComputeId: Enum for the different types of compute capabilities within Ritual's
        services.

    Attributes:
        ML: Machine Learning Compute
        ZK: Zero Knowledge Compute
        TEE: Trusted Execution Environment Compute
    """

    ML = "ml"
    ZK = "zk"
    TEE = "tee"


class MLTask(StrEnum):
    """
    MLTask: Enum for the different types of machine learning tasks that can be
    supported. This is provided for utility & should not be used as a strict
    validation mechanism.

    Attributes:
        TextGeneration: Text Generation
        TextClassification: Text Classification
        TokenClassification: Token Classification
        Summarization: Summarization
        ImageClassification: Image Classification
        ImageSegmentation: Image Segmentation
        ObjectDetection: Object Detection
    """

    TextGeneration = "text_generation"
    TextClassification = "text_classification"
    TokenClassification = "token_classification"
    Summarization = "summarization"
    ImageClassification = "image_classification"
    ImageSegmentation = "image_segmentation"
    ObjectDetection = "object_detection"


class CSSModel(BaseModel):
    owner: CSSProvider
    name: str

    @property
    def unique_id(self) -> str:
        return f"{self.owner}/{self.name}"

    @classmethod
    def from_unique_id(cls, unique_id: str) -> CSSModel:
        parts = unique_id.split("/")
        owner = CSSProvider(parts[0])
        model_name = parts[1]
        return cls(owner=owner, name=model_name)


class MLComputeCapability(BaseModel):
    """
    MLComputeCapability: Class for the machine learning compute capabilities within
        Ritual's services.

    Attributes:
        id (Literal[ComputeId.ML]): The type of compute capability
        type (MLType): The type of machine learning model that can be supported
        task (List[MLTask]): The list of machine learning tasks that can be supported
        models (List[BroadcastedArtifact] | List[CSSModel]): The list of models that can
            be supported
        cached_models (List[BroadcastedArtifact]): The list of cached models that can
            be supported
        inference_engine (Optional[str]): The inference engine that can be supported
        inference_engine_version (Optional[str]): The inference engine version that can
            be supported
    """

    id: Literal[ComputeId.ML] = ComputeId.ML
    type: MLType
    task: List[MLTask]
    models: List[BroadcastedArtifact] | List[CSSModel] = []
    cached_models: List[BroadcastedArtifact] = []
    inference_engine: Optional[str] = None
    inference_engine_version: Optional[str] = None

    @classmethod
    def onnx_compute(
        cls,
        models: Optional[List[BroadcastedArtifact]] = None,
        cached_models: Optional[List[BroadcastedArtifact]] = None,
    ) -> MLComputeCapability:
        """
        Utility function to generate an ONNX compute capability.

        Args:
            models (Optional[List[BroadcastedArtifact]]): The list of models that can be
                supported
            cached_models (Optional[List[BroadcastedArtifact]]): The list of cached
                models

        Returns:
            MLComputeCapability: The ONNX compute capability
        """
        models = models or []
        cached_models = cached_models or []
        return cls(
            type=MLType.ONNX,
            task=[],
            models=models,
            cached_models=cached_models,
        )

    @classmethod
    def llama_cpp_compute(
        cls, models: Optional[List[CachedArtifact]] = None
    ) -> MLComputeCapability:
        """
        Utility function to generate a llama.cpp compute capability.

        Args:
            models (Optional[List[CachedArtifact]]): The list of models that can be
                supported

        Returns:
            MLComputeCapability: The llama.cpp compute capability
        """
        try:
            version = " ".join(
                subprocess.check_output(
                    shlex.split("llama-server --version"), stderr=subprocess.STDOUT
                )
                .decode("utf-8")
                .strip()
                .split("\n")
            )
        except subprocess.CalledProcessError as e:
            version = e.output.decode("utf-8")
        _models: List[CachedArtifact] = models or []
        __models = [m.to_broadcasted_artifact() for m in _models]
        return cls(
            type=MLType.LLAMA_CPP,
            task=[MLTask.TextGeneration],
            models=__models,
            cached_models=__models,
            inference_engine="llama_cpp",
            inference_engine_version=version,
        )

    @classmethod
    def torch_compute(
        cls,
        models: Optional[List[BroadcastedArtifact]] = None,
        cached_models: Optional[List[BroadcastedArtifact]] = None,
    ) -> MLComputeCapability:
        """
        Utility function to generate a Torch compute capability.

        Args:
            models (Optional[List[BroadcastedArtifact]]): The list of models that can be
                supported
            cached_models (Optional[List[BroadcastedArtifact]]): The list of cached
                models

        Returns:
            MLComputeCapability: The torch compute capability
        """
        models = models or []
        cached_models = cached_models or []
        return cls(
            type=MLType.TORCH,
            task=[],
            models=models,
            cached_models=cached_models,
        )

    @classmethod
    def hf_client_compute(
        cls,
    ) -> MLComputeCapability:
        """
        Utility function to generate a Huggingface client compute capability.
        """
        return cls(
            type=MLType.HF_CLIENT,
            task=[
                MLTask.TextGeneration,
                MLTask.TextClassification,
                MLTask.TokenClassification,
                MLTask.Summarization,
            ],
        )

    @classmethod
    def tgi_client_compute(
        cls,
    ) -> MLComputeCapability:
        """
        Utility function to generate a TGI client compute capability.
        """
        return cls(
            type=MLType.TGI_CLIENT,
            task=[MLTask.TextGeneration],
        )

    @classmethod
    def css_compute(
        cls,
        models: Optional[List[CSSModel]] = None,
    ) -> MLComputeCapability:
        """
        Utility function to generate a CSS compute capability.

        Args:
            models (Optional[List[CSSModel]]): The list of models that can be supported

        Returns:
            MLComputeCapability: The CSS compute capability
        """
        models = models or []
        return cls(
            type=MLType.CSS,
            task=[],
            models=models,
        )


class ZKComputeCapability(BaseModel):
    """
    ZKComputeCapability: Class for the zero knowledge compute capabilities within
        Ritual's services..

    Attributes:
        id (Literal[ComputeId.ZK]): The type of compute capability
    """

    id: Literal[ComputeId.ZK] = ComputeId.ZK


ComputeCapability = Annotated[
    Union[
        Annotated[MLComputeCapability, Tag("id")],
        Annotated[ZKComputeCapability, Tag("id")],
        # other types: zk, tee, etc.
    ],
    Discriminator("id"),
]


class CPUCore(BaseModel):
    """
    CPUCore: Class representation for the CPU core information

    Attributes:
        id (int): The id of the core, e.g. 0
        frequency (float): The frequency of the core
        max_frequency (float): The maximum frequency of the core
        min_frequency (float): The minimum frequency of the core
    """

    id: int
    frequency: float
    max_frequency: Optional[float] = None
    min_frequency: Optional[float] = None


class CPUInfo(BaseModel):
    """
    CPUInfo: Class representation for the CPU information

    Attributes:
        model (str): The model of the CPU, e.g. Intel(R) Core(TM) i7-7700HQ CPU
        architecture (str): The architecture of the CPU, e.g. x86_64
        byte_order (str): The byte order of the CPU, e.g. Little Endian
        vendor_id (str): The vendor id of the CPU, e.g. GenuineIntel
        num_cores (int): The number of cores in the CPU
        cores (List[CPUCore]): The list of cores in the CPU
    """

    model: str
    architecture: str
    byte_order: str
    vendor_id: str
    num_cores: int

    cores: List[CPUCore]

    @classmethod
    def read_from_linux(cls) -> CPUInfo:
        """
        Reads the CPU information from a Linux system

        Returns:
            CPUInfo: The CPU information
        """
        os.system("lscpu -J > /tmp/lscpu.json")
        model, num_cores, vendor_id, byte_order, architecture = "", 0, "", "", ""

        with open("/tmp/lscpu.json") as f:
            lscpu = json.load(f)
            for info in lscpu["lscpu"]:
                if "model name" in info["field"].lower():
                    model = info["data"]
                if "cpu(s):" == info["field"].lower():
                    num_cores = info["data"]
                if "vendor id" in info["field"].lower():
                    vendor_id = info["data"]
                if "byte order" in info["field"].lower():
                    byte_order = info["data"]
                if "architecture" in info["field"].lower():
                    architecture = info["data"]

        cpu_info = []
        try:
            processor = None
            with open("/proc/cpuinfo", "r") as f:
                for line in f:
                    if "processor" in line:
                        processor = int(line.split(":")[1].strip())
                    if "cpu MHz" in line:
                        frequency = float(line.split(":")[1].strip())
                        if processor is not None:
                            cpu_info.append(CPUCore(id=processor, frequency=frequency))

        except FileNotFoundError:
            print("/proc/cpuinfo not found.")

        return cls(
            model=model,
            num_cores=num_cores,
            vendor_id=vendor_id,
            byte_order=byte_order,
            architecture=architecture,
            cores=cpu_info,
        )

    @classmethod
    def read_from_darwin(cls) -> CPUInfo:
        """
        Reads the CPU information from a Darwin system

        Returns:
            CPUInfo: The CPU information
        """
        os.system("sysctl -a > /tmp/sysctl_info")
        model, num_cores, vendor_id, byte_order, architecture = "", 0, "", "", ""

        with open("/tmp/sysctl_info") as f:
            for line in f:
                if line.startswith("machdep.cpu.brand_string"):
                    model = line.split(":")[1].strip()
                if line.startswith("machdep.cpu.core_count"):
                    num_cores = int(line.split(":")[1].strip())
                if line.startswith("machdep.cpu.brand_string"):
                    vendor_id = line.split(":")[1].strip()
                if line.startswith("hw.byteorder"):
                    byte_order = line.split(":")[1].strip()

        architecture = subprocess.check_output(["uname", "-m"]).decode("utf-8").strip()
        frequency_ = (
            subprocess.check_output(["sysctl", "-n", "hw.cpufrequency"])
            .decode("utf-8")
            .strip()
        )
        frequency = float(frequency_) if frequency_ else 0.0

        cpu_info = []
        try:
            # Get the number of CPU cores
            num_cores = int(
                subprocess.check_output(["sysctl", "-n", "hw.ncpu"]).strip()
            )
            for core_id in range(num_cores):
                cpu_info.append(CPUCore(id=core_id, frequency=frequency))

        except subprocess.CalledProcessError as e:
            print(f"Error retrieving CPU information: {e}")

        return cls(
            model=model,
            num_cores=num_cores,
            vendor_id=vendor_id,
            byte_order=byte_order,
            architecture=architecture,
            cores=cpu_info,
        )

    @classmethod
    def read_from_system(cls) -> CPUInfo:
        """
        Reads the CPU information from the system. Automatically detects the OS and
        reads the CPU information accordingly.

        Returns:
            CPUInfo: The CPU information
        """
        match platform.system().lower():
            case "linux":
                return cls.read_from_linux()
            case "darwin":
                return cls.read_from_darwin()
            case _:
                return cls.read_from_linux()


class OSInfo(BaseModel):
    """
    OSInfo: Class representation for the OS information

    Attributes:
        name (str): The name of the OS, e.g. Ubuntu
        version (str): The version of the OS
    """

    name: str
    version: str

    @classmethod
    def read_from_system(cls) -> OSInfo:
        """
        Reads the OS information from the system

        Returns:
            OSInfo: The OS information
        """
        return cls(name=platform.system(), version=platform.version())


class DiskInfo(BaseModel):
    """
    DiskInfo: Class representation for the Disk information

    Attributes:
        filesystem (str): The filesystem of the disk, e.g. ext4
        mount_point (str): The mount point of the disk, e.g. /
        size (int): The size of the disk in bytes
        used (int): The used space on the disk in bytes
        available (int): The available space on the disk in bytes
    """

    filesystem: str
    mount_point: str
    size: int
    used: int
    available: int

    @classmethod
    def read_from_system(cls) -> List[DiskInfo]:
        """
        Reads the disk information from the system

        Returns:
            List[DiskInfo]: The disk information
        """
        os.system("df > /tmp/df_info")
        disk_info = []
        with open("/tmp/df_info") as f:
            for line in f:
                if line.startswith("Filesystem") or line.startswith("map"):
                    continue
                fields = line.split()
                match platform.system().lower():
                    case "linux":
                        disk_info.append(
                            cls(
                                filesystem=fields[0],
                                mount_point=fields[5],
                                size=int(fields[1]),
                                used=int(fields[2]),
                                available=int(fields[3]),
                            )
                        )
                    case "darwin":
                        disk_info.append(
                            cls(
                                filesystem=fields[0],
                                mount_point=fields[8],
                                size=int(fields[1]),
                                used=int(fields[2]),
                                available=int(fields[3]),
                            )
                        )
        return disk_info


class GPUInfo(BaseModel):
    """
    GPUInfo: Class representation for the GPU information

    Attributes:
        name (str): The name of the GPU, e.g. NVIDIA GeForce GTX 1080
        memory_total (int): The total memory of the GPU in bytes
        memory_used (int): The used memory of the GPU in bytes
        cuda_device_id (Optional[int]): The CUDA device id of the GPU
    """

    name: str
    memory_total: int
    memory_used: int
    cuda_device_id: Optional[int] = None


class HardwareCapabilityId(StrEnum):
    """
    HardwareCapabilityType: Enum for the different types of hardware capabilities within
        Ritual's services..

    Attributes:
        Base: Generic Hardware Capability, contains information about the OS, CPU, and
            disk
        GPU: Graphics Processing Unit
        TEE: Trusted Execution Environment
    """

    Base = "base"
    GPU = "gpu"
    TEE = "tee"


class GenericHardwareCapability(BaseModel):
    capability_id: Literal[HardwareCapabilityId.Base] = HardwareCapabilityId.Base
    os_info: OSInfo
    cpu_info: CPUInfo
    disk_info: List[DiskInfo]

    @classmethod
    def read_from_system(cls) -> "GenericHardwareCapability":
        """
        Reads the generic hardware capability from the system

        Returns:
            GenericHardwareCapability: The generic hardware capability
        """
        return cls(
            os_info=OSInfo.read_from_system(),
            cpu_info=CPUInfo.read_from_system(),
            disk_info=DiskInfo.read_from_system(),
        )


class GPUHardwareCapability(BaseModel):
    capability_id: Literal[HardwareCapabilityId.GPU] = HardwareCapabilityId.GPU
    driver_version: str
    cuda_version: str
    gpu_info: List[GPUInfo]

    @classmethod
    def read_from_system(cls) -> Optional[GPUHardwareCapability]:
        """
        Reads the GPU hardware capability from the system

        Returns:
            Optional[GPUHardwareCapability]: The GPU hardware capability
        """
        import subprocess
        import xml.etree.ElementTree as ET

        def parse_memory(mem_str: str | None) -> int:
            if mem_str is None:
                return 0
            value_, unit = mem_str.split()
            value = int(value_)
            if unit == "MiB":
                return value * 1024 * 1024
            elif unit == "GiB":
                return value * 1024 * 1024 * 1024
            return value

        try:
            result = subprocess.run(
                ["nvidia-smi", "-q", "-x"], capture_output=True, text=True
            )

            if result.returncode != 0:
                log.info("could not run nvidia-smi, skipping GPU info")
                return None
        except FileNotFoundError:
            log.info("nvidia-smi not found, skipping GPU info")
            return None

        root = ET.fromstring(result.stdout)

        driver_version = root.findtext("driver_version")
        cuda_version = root.findtext("cuda_version")

        def _find(gpu: Element, field: str) -> str | None:
            f = gpu.find(field)
            if f is None:
                return None
            return f.text

        gpu_info = [
            GPUInfo(
                name=gpu.findtext("product_name", "N/A"),
                memory_total=parse_memory(_find(gpu, "fb_memory_usage/total")),
                memory_used=parse_memory(_find(gpu, "fb_memory_usage/used")),
                cuda_device_id=int(gpu.findtext("minor_number", "-1")),
            )
            for gpu in root.findall("gpu")
        ]

        return cls(
            driver_version=driver_version or "N/A",
            cuda_version=cuda_version or "N/A",
            gpu_info=gpu_info,
        )


class TEEHardwareCapability(BaseModel):
    capability_id: Literal[HardwareCapabilityId.TEE] = HardwareCapabilityId.TEE


HardwareCapability = Annotated[
    Union[
        Annotated[GenericHardwareCapability, Tag("capability_id")],
        Annotated[GPUHardwareCapability, Tag("capability_id")],
        Annotated[TEEHardwareCapability, Tag("capability_id")],
    ],
    Discriminator("capability_id"),
]


def read_hw_cap_from_system() -> List[HardwareCapability]:
    """
    Reads the hardware capabilities from the system.

    """
    capabilities: List[HardwareCapability] = [
        GenericHardwareCapability.read_from_system()
    ]
    if gpu_capability := GPUHardwareCapability.read_from_system():
        capabilities.append(gpu_capability)
    return capabilities


class ServiceResources(BaseModel):
    """
    ServiceResources: Class representation for the resources of a service within
        Ritual's services..

    Attributes:
        service_id (str): The unique identifier for the service
        hardware_capabilities (List[HardwareCapability]): The list of hardware
            capabilities of the service
        compute_capability (List[ComputeCapability]): The list of compute capabilities
            of the service
    """

    version: str = "0.1.0"
    service_id: str

    hardware_capabilities: List[HardwareCapability]
    compute_capability: List[ComputeCapability]

    @classmethod
    def initialize(
        cls,
        service_id: str,
        compute_capability: List[ComputeCapability],
    ) -> ServiceResources:
        """
        Initializes the service resources. Reads the hardware capabilities from the
        system.

        Args:
            service_id (str): The unique identifier for the service
            compute_capability (List[ComputeCapability]): The list of compute
                capabilities of the service

        Returns:
            ServiceResources: The service resources
        """
        return cls(
            service_id=service_id,
            hardware_capabilities=read_hw_cap_from_system(),
            compute_capability=compute_capability,
        )


class Resource(BaseModel):
    """
    Resource: Class representation for the resources of a service within Ritual's
        services.

    Attributes:
        capabilities (List[Capability]): The list of capabilities of the service
        version (str): The version of this specification
    """

    capabilities: List[ServiceResources]
    version: str
