import os
import logging
import time
import argparse
import json

from register_model import _register_model

# Allowed log levels
VALID_LOG_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

# Read from environment variable
LOG_LEVEL_STR = os.getenv("LOG_LEVEL", "WARNING").upper()

# Create a logger for this module
_log = logging.getLogger(__name__)

def main():
    # Validate and set level
    if LOG_LEVEL_STR in VALID_LOG_LEVELS:
        log_level = getattr(logging, LOG_LEVEL_STR)
    else:
        print(f"Invalid LOG_LEVEL '{LOG_LEVEL_STR}' - defaulting to WARNING")
        log_level = logging.WARNING

    logging.basicConfig(level=log_level)

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Test model registration with the model registry.")
    
    parser.add_argument(
        '--model-registry-name',
        required=True,
        help='Name of the model registry'
    )

    parser.add_argument(
        '--model-registry-namespace',
        required=True,
        help='Namespace of the model registry'
    )

    parser.add_argument(
        '--model-name',
        required=True,
        help='Name of the model'
    )

    parser.add_argument(
        '--model-uri',
        required=True,
        help='URI of the model'
    )

    parser.add_argument(
        '--model-version',
        required=True,
        help='Version of the model'
    )

    parser.add_argument(
        '--model-description',
        required=False,
        default='Test model registration',
        help='Description of the model'
    )

    parser.add_argument(
        '--model-format-name',
        required=False,
        default='pytorch',
        help='Model format name'
    )

    parser.add_argument(
        '--model-format-version',
        required=False,
        default='1',
        help='Model format version'
    )

    parser.add_argument(
        '--author',
        required=False,
        default='test-user',
        help='Author of the model'
    )

    parser.add_argument(
        '--owner',
        required=False,
        default='test-owner',
        help='Owner of the model'
    )

    parser.add_argument(
        '--labels',
        required=False,
        default='{}',
        help='Labels for the model as a JSON string'
    )

    args = parser.parse_args()

    print(f"Model registry name: {args.model_registry_name}")
    print(f"Istio system namespace: {args.model_registry_namespace}")
    print(f"Model name: {args.model_name}")
    print(f"Model URI: {args.model_uri}")
    print(f"Model version: {args.model_version}")
    print(f"Model description: {args.model_description}")
    print(f"Model format name: {args.model_format_name}")
    print(f"Model format version: {args.model_format_version}")
    print(f"Author: {args.author}")
    print(f"Owner: {args.owner}")
    print(f"Labels: {args.labels}")

    # Start the timer
    start_time = time.time()

    try:
        # Register the model
        model_id, model_version_id = _register_model(
            model_registry_name=args.model_registry_name,
            model_registry_namespace=args.model_registry_namespace,
            model_name=args.model_name,
            model_uri=args.model_uri,
            model_version=args.model_version,
            model_description=args.model_description,
            model_format_name=args.model_format_name,
            model_format_version=args.model_format_version,
            author=args.author,
            owner=args.owner,
            labels=args.labels
        )

        results = json.dumps({
            "model_id": model_id,
            "model_version_id": model_version_id,
            "success": True
        })

        # Log the results
        _log.info(f"Registration results: {results}")
        print(f"Model registered successfully!")
        print(f"Model ID: {model_id}")
        print(f"Model Version ID: {model_version_id}")

    except Exception as e:
        _log.error(f"Model registration failed: {e}")
        print(f"Model registration failed: {e}")
        results = json.dumps({
            "success": False,
            "error": str(e)
        })

    # Stop the timer
    end_time = time.time() - start_time

    _log.info(f"Model registration completed in {end_time:.2f} seconds.")
    print(f"Model registration completed in {end_time:.2f} seconds.")
    
if __name__ == "__main__":
    main()