import os
import json
import re

from kfp import compiler

from kfp.dsl import Input, Metrics, OutputPath
from kfp import dsl

# Load environment variables with load_dotenv
from load_dotenv import load_dotenv
load_dotenv()

# Set environment variables
BASE_IMAGE = os.environ.get("BASE_IMAGE", "python:3.11-slim-bullseye")
NAMESPACE = os.environ.get("NAMESPACE", "default")
REGISTRY = os.environ.get("REGISTRY", f"image-registry.openshift-image-registry.svc:5000/{NAMESPACE}")

TARGET_IMAGE = f"{REGISTRY}/register_model:latest"

MODEL_REGISTRY_PIP_VERSION="0.2.13"
K8S_PIP_VERSION="23.6.0"
LOAD_DOTENV_PIP_VERSION="0.1.0"
BOTOCORE_PIP_VERSION="1.35.54"
BOTO3_PIP_VERSION="1.35.54"

# This component registers a model in the model registry and returns the model ID
@dsl.component(
    base_image=BASE_IMAGE,
    target_image=TARGET_IMAGE,
    packages_to_install=[f"model_registry=={MODEL_REGISTRY_PIP_VERSION}",
                         f"kubernetes=={K8S_PIP_VERSION}",
                         f"load_dotenv=={LOAD_DOTENV_PIP_VERSION}",
                         f"botocore=={BOTOCORE_PIP_VERSION}",
                         f"boto3=={BOTO3_PIP_VERSION}"],
)
def register_model(
    model_registry_name: str,  # Name of the model registry
    istio_system_namespace: str,      # Namespace of the istio system namespace

    model_name: str,           # Name of the model
    model_uri: str,            # Path to the model file
    model_version: str,        # Version of the model
    model_description: str,    # Description of the model
    model_format_name: str,    # Model format name
    model_format_version: str, # Model format version
    author: str,               # Author of the model
    owner: str,                # Owner of the model
    labels: str,               # Labels for the model as a json string
    input_metrics: Input[Metrics],         # Input metrics
    output_model_id: OutputPath(str),         # type: ignore
    output_model_version_id: OutputPath(str), # type: ignore
):
    from utils import get_token, metrics_to_dict, get_model_registry_endpoint

    from model_registry import ModelRegistry

    # Get the model registry endpoint
    model_registry_endpoint = get_model_registry_endpoint(model_registry_name, istio_system_namespace)
    if model_registry_endpoint is None:
        raise ValueError("Model registry endpoint not found.")

    # Print the model registry endpoint
    print(f"Model registry endpoint: {model_registry_endpoint}")

    # Check the uri and return a value error if it is not a valid uri and the protocol is s3, http, https or oci
    if not model_uri.startswith("s3://") and not model_uri.startswith("http://") and not model_uri.startswith("https://") and not model_uri.startswith("oci://"):
        raise ValueError("Invalid model URI. Supported protocols are s3, http, https, and oci.")

    # Generate metadata from the input metrics
    metadata = metrics_to_dict(input_metrics)

    # Check if labels is a non-empty string
    if labels and labels.strip():
        # If the labels is not a valid json string, return a value error
        try:
            # Add labels to the metadata
            labels = json.loads(labels)
            for key, value in labels.items():
                metadata[key] = value
        except json.JSONDecodeError:
            raise ValueError("Invalid labels. Labels must be a valid JSON string.")

    # Convert the metadata values to strings
    metadata = {key: str(value) for key, value in metadata.items()}

    # Print the metadata
    print(f"Metadata: {metadata}")

    # Create the model registry object
    registry = ModelRegistry(model_registry_endpoint, author="register_model", user_token=get_token())

    # Register the model
    model = registry.register_model(
        name=model_name,                           # model name
        author=author,                             # author of the model
        owner=owner,                               # owner of the model
        uri=model_uri,                             # model URI
        version=model_version,                     # model version
        description=model_description,             # description of the model
        model_format_name=model_format_name,       # model format: onnx, pytorch, tensorflow, etc.
        model_format_version=model_format_version, # model format version: 1, 2, 3, etc.
        metadata=metadata
    )

    # Isolate the labels with no values
    tags = {key: value for key, value in metadata.items() if not value}

    # Add the tags to the model as cusom properties
    model.custom_properties = tags
    model.description = model_description

    # Save the model
    registry.update(model)
    
    # Retrieve the model version
    model_version = registry.get_model_version(model_name, model_version)

    # Save the model ID to the output path
    with open(output_model_id, 'w') as file:
        file.write(model.id)

    # Save the model version to the output path
    with open(output_model_version_id, 'w') as file:
        file.write(model_version.id)
    
    
if __name__ == "__main__":
    # Generate and save the component YAML file
    component_package_path = __file__.replace('.py', '.yaml')

    compiler.Compiler().compile(
        pipeline_func=register_model,
        package_path=component_package_path
    )
