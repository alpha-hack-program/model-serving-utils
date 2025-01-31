#!/bin/sh

# Load .env file
set -a
. .env

# Arguments: [llama|granite] [8b] [3.0|3.1|3.2]
if [ "$#" -ne 3 ]; then
  echo "Usage: undeploy-model.sh [llama|granite] [8b] [3.0|3.1|3.2]"
  exit 1
fi

# Extract model family from the first argument
MODEL_FAMILY="$1"

# Extract model size from the second argument
MODEL_SIZE="$2"

# Extract model version from the third argument
MODEL_VERSION="$3"

# Delete the application object
oc delete application ${MODEL_FAMILY}-${MODEL_VERSION}-${MODEL_SIZE} -n ${ARGOCD_NAMESPACE}