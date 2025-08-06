#!/bin/bash

# Set PYTHONPATH to the components directory (parent of both shared and register_model)
export PYTHONPATH=$(cd "$(dirname "$0")"/../../ && pwd)

# Set default environment variables for model registration
export MODEL_REGISTRY_NAME=${MODEL_REGISTRY_NAME:-"model-registry"}
export ISTIO_SYSTEM_NAMESPACE=${ISTIO_SYSTEM_NAMESPACE:-"istio-system"}

# Get token using `oc whoami -t`
export TOKEN=$(oc whoami -t)

# Write the token to a file .token
echo $TOKEN > .token

# Run the test script with DEBUG log level with all the arguments
TOKEN_PATH=$(pwd)/.token LOG_LEVEL=DEBUG python test.py $@

# Clean up the token file
rm -f .token