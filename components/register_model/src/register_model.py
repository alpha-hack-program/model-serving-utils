import os
import json
import logging

from kfp import compiler

from kfp.dsl import Input, OutputPath
from kfp import dsl

from shared.utils import get_model_registry_endpoint
from shared.kubeflow import get_token

from model_registry import ModelRegistry

# Load environment variables with load_dotenv
from load_dotenv import load_dotenv
load_dotenv()

# Set environment variables
NAMESPACE=os.environ.get("NAMESPACE", "default")
COMPONENT_NAME=os.getenv("COMPONENT_NAME", f"register_model")
BASE_IMAGE=os.getenv("BASE_IMAGE", "python:3.11-slim-bullseye")
REGISTRY=os.environ.get("REGISTRY", f"image-registry.openshift-image-registry.svc:5000/{NAMESPACE}")
TAG=os.environ.get("TAG", f"latest")
TARGET_IMAGE=f"{REGISTRY}/{COMPONENT_NAME}:{TAG}"

# MODEL_REGISTRY_PIP_VERSION="0.3.6"
# K8S_PIP_VERSION="23.6.0"
# LOAD_DOTENV_PIP_VERSION="0.1.0"
# BOTOCORE_PIP_VERSION="1.35.54"
# BOTO3_PIP_VERSION="1.35.54"

# Allowed log levels
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

# Read from environment variable
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "WARNING").upper()

# Create a logger for this module
_log = logging.getLogger(__name__)

def _register_model(
    model_registry_name: str,  # Name of the model registry
    model_registry_namespace: str,      # Namespace of the model registries

    model_name: str,           # Name of the model
    model_uri: str,            # Path to the model file
    model_version: str,        # Version of the model
    model_description: str,    # Description of the model
    model_format_name: str,    # Model format name
    model_format_version: str, # Model format version
    author: str,               # Author of the model
    owner: str,                # Owner of the model
    labels: str,               # Labels for the model as a json string
) -> tuple[str, str]:
    """
    Register a model in the model registry.
    Args:
        model_registry_name (str): Name of the model registry
        model_registry_namespace (str): Namespace of the model registries namespace
        model_name (str): Name of the model
        model_uri (str): Path to the model file
        model_version (str): Version of the model
        model_description (str): Description of the model
        model_format_name (str): Model format name
        model_format_version (str): Model format version
        author (str): Author of the model
        owner (str): Owner of the model
        labels (str): Labels for the model as a json string
    Returns:
        tuple[str, str]: A tuple containing (model_id, model_version_id)
    """
    # Log input parameters
    _log.info(f"Model registry name: {model_registry_name}")
    _log.info(f"Model registry namespace: {model_registry_namespace}")
    _log.info(f"Model name: {model_name}")
    _log.info(f"Model URI: {model_uri}")
    _log.info(f"Model version: {model_version}")
    _log.info(f"Model description: {model_description}")
    _log.info(f"Model format name: {model_format_name}")
    _log.info(f"Model format version: {model_format_version}")
    _log.info(f"Author: {author}")
    _log.info(f"Owner: {owner}")
    _log.info(f"Labels: {labels}")

    # Get the model registry endpoint
    model_registry_endpoint = get_model_registry_endpoint(model_registry_name, model_registry_namespace)
    if model_registry_endpoint is None:
        _log.error("Model registry endpoint not found.")
        raise ValueError("Model registry endpoint not found.")

    # Log the model registry endpoint
    _log.info(f"Model registry endpoint: {model_registry_endpoint}")

    # Check the uri and return a value error if it is not a valid uri and the protocol is s3, http, https or oci
    if not model_uri.startswith("s3://") and not model_uri.startswith("http://") and not model_uri.startswith("https://") and not model_uri.startswith("oci://"):
        _log.error(f"Invalid model URI: {model_uri}. Supported protocols are s3, http, https, and oci.")
        raise ValueError("Invalid model URI. Supported protocols are s3, http, https, and oci.")

    # Generate metadata dict
    metadata = {}

    # Check if labels is a non-empty string
    if labels and labels.strip():
        # If the labels is not a valid json string, return a value error
        try:
            # Parse labels from JSON string to dict
            labels_dict = json.loads(labels)
            for key, value in labels_dict.items():
                metadata[key] = value
            _log.info(f"Parsed labels: {labels_dict}")
        except json.JSONDecodeError as e:
            _log.error(f"Invalid labels JSON: {labels}. Error: {e}")
            raise ValueError("Invalid labels. Labels must be a valid JSON string.")

    # Convert the metadata values to strings
    metadata = {key: str(value) for key, value in metadata.items()}

    # Log the metadata
    _log.info(f"Metadata: {metadata}")

    # Create the model registry object
    # ModelRegistry requires is_secure=False and port=80 for HTTP (no TLS) routes
    _log.info("Creating model registry client...")
    if model_registry_endpoint.startswith("http://"):
        registry = ModelRegistry(
            model_registry_endpoint,
            80,
            author="register_model",
            is_secure=False,
            user_token=get_token(),
        )
    else:
        registry = ModelRegistry(
            model_registry_endpoint,
            author="register_model",
            user_token=get_token(),
        )

    # Register the model
    _log.info(f"Registering model '{model_name}' version '{model_version}'...")
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

    # Check if the model was registered successfully
    if model is None:
        _log.error("Model registration failed.")
        raise ValueError("Model registration failed. Please check the model registry endpoint and the model parameters.")
    # Get the model ID
    if model.id is None:
        _log.error("Model ID is None after registration.")
        raise ValueError("Model ID is None. Please check the model registration parameters.")
    
    _log.info(f"Model registered successfully with ID: {model.id}")
    
    # Isolate the labels with no values
    tags = {key: value for key, value in metadata.items() if not value}

    # Add the tags to the model as custom properties
    model.custom_properties = tags
    model.description = model_description

    # Save the model
    _log.info("Updating model with custom properties...")
    registry.update(model)
    
    # Retrieve the model version
    _log.info(f"Retrieving model version '{model_version}' for model '{model_name}'...")
    model_version_obj = registry.get_model_version(model_name, model_version)
    if model_version_obj is None:
        _log.error(f"Model version {model_version} not found for model {model_name}.")
        raise ValueError(f"Model version {model_version} not found for model {model_name}.")
    # Check if the model version ID is None
    if model_version_obj.id is None:
        _log.error("Model version ID is None.")
        raise ValueError("Model version ID is None. Please check the model registration parameters.")

    _log.info(f"Model version retrieved successfully with ID: {model_version_obj.id}")

    return model.id, model_version_obj.id

# This component registers a model in the model registry and returns the model ID
@dsl.component(
    base_image=BASE_IMAGE,
    target_image=TARGET_IMAGE,
)
def register_model(
    model_registry_name: str,  # Name of the model registry
    model_registry_namespace: str,      # Namespace of the model registries

    model_name: str,           # Name of the model
    model_uri: str,            # Path to the model file
    model_version: str,        # Version of the model
    model_description: str,    # Description of the model
    model_format_name: str,    # Model format name
    model_format_version: str, # Model format version
    author: str,               # Author of the model
    owner: str,                # Owner of the model
    labels: str,               # Labels for the model as a json string
    output_model_id: OutputPath(str),         # type: ignore
    output_model_version_id: OutputPath(str), # type: ignore
):
    """
    Register a model in the model registry and save the model ID and version ID to output paths.
    """
    # Call the private function to register the model
    model_id, model_version_id = _register_model(
        model_registry_name=model_registry_name,
        model_registry_namespace=model_registry_namespace,
        model_name=model_name,
        model_uri=model_uri,
        model_version=model_version,
        model_description=model_description,
        model_format_name=model_format_name,
        model_format_version=model_format_version,
        author=author,
        owner=owner,
        labels=labels,
    )

    # Save the model ID to the output path
    with open(output_model_id, 'w') as file:
        file.write(model_id)

    # Save the model version to the output path
    with open(output_model_version_id, 'w') as file:
        file.write(model_version_id)
    
    
if __name__ == "__main__":
    # Generate and save the component YAML file
    component_package_path = __file__.replace('.py', '.yaml')

    compiler.Compiler().compile(
        pipeline_func=register_model,
        package_path=component_package_path
    )