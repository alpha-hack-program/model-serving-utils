#!/bin/bash

# Set PYTHONPATH to the components directory (parent of both shared and register_model)
export PYTHONPATH=$(cd "$(dirname "$0")"/../../ && pwd)

# Set default environment variables for model registration (OpenShift AI default)
export MODEL_REGISTRY_NAME=${MODEL_REGISTRY_NAME:-"model-registry-dev"}
export MODEL_REGISTRY_NAMESPACE=${MODEL_REGISTRY_NAMESPACE:-"rhoai-model-registries"}

# Get token using `oc whoami -t`
export TOKEN=$(oc whoami -t)

# Write the token to a file .token
echo $TOKEN > .token

# Run the test script with DEBUG log level.
# Pass registry defaults first; $@ overrides (e.g. for custom model params).
# Example:
#   ./test.sh --model-name model1 --model-version 1.0 --model-uri s3://bucket/model1/model.onnx \
#     --model-description "cool model" --model-format-name onnx --model-format-version "1" \
#     --author "Carlos V" --owner "John Doe" --labels "type=vision,accuracy=0.9"
TOKEN_PATH=$(pwd)/.token LOG_LEVEL=DEBUG python test.py \
  --model-registry-name "$MODEL_REGISTRY_NAME" \
  --model-registry-namespace "$MODEL_REGISTRY_NAMESPACE" \
  "$@"

# Clean up the token file
rm -f .token