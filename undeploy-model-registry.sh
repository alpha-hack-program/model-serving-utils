#!/bin/sh

# Load .env file
set -a
. .env

# Arguments: name_of_registry
if [ "$#" -ne 1 ]; then
  echo "Usage: deploy-model-registry.sh name_of_registry"
  exit 1
fi

MODEL_REGISTRY_NAME="$1"

# Delete the application object
oc delete application model-registry-${MODEL_REGISTRY_NAME} -n ${ARGOCD_NAMESPACE}