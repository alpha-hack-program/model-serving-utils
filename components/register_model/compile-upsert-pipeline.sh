#!/bin/bash

# Load base environment
. $(dirname "$(pwd)")/.env

# Source the component-specific environment variables if the file exists
[ -f ./.env ] && . ./.env

# COMPONENT_NAME should be the name of the folder in components folder
export COMPONENT_NAME="$(basename "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)")"

echo "Compiling test pipeline for COMPONENT_NAME ${COMPONENT_NAME}"

# Export variables needed while compiling the pipeline
export BASE_IMAGE REGISTRY TAG
export PYTHONPATH=$(pwd)/src:$(dirname "$(pwd)")

COMPILED_COMPONENT=$(pwd)/src/component_metadata/${COMPONENT_NAME}.yaml

# Check if COMPILED_COMPONENT file exists
if [ -f "${COMPILED_COMPONENT}" ]; then
    echo "COMPILED_COMPONENT ${COMPILED_COMPONENT} found."
else
    echo "COMPILED_COMPONENT ${COMPILED_COMPONENT} not found."
    echo "Please go to $(dirname "$(pwd)") and run $ ./build-component.sh ${COMPONENT_NAME}"
    exit 1
fi

TOKEN=$(oc whoami -t)

# If TOKEN is empty print error and exit
if [ -z "$TOKEN" ]; then
  echo "Error: No token found. Please login to OpenShift using 'oc login' command."
  echo "Compile only mode."

  python pipeline.py

  exit 1
fi

DATA_SCIENCE_PROJECT_NAMESPACE=$(oc project --short)

# If DATA_SCIENCE_PROJECT_NAMESPACE is empty print error and exit
if [ -z "$DATA_SCIENCE_PROJECT_NAMESPACE" ]; then
  echo "Error: No namespace found. Please set the namespace in bootstrap/.env file."
  exit 1
fi

DSPA_HOST=$(oc get route ds-pipeline-dspa -n ${DATA_SCIENCE_PROJECT_NAMESPACE} -o jsonpath='{.spec.host}')

echo "DSPA_HOST: $DSPA_HOST"

# If DSPA_HOST is empty print error and exit
if [ -z "$DSPA_HOST" ]; then
  echo "Error: No host found for ds-pipeline-dspa. Please check if the deployment is successful."
  exit 1
fi

python pipeline.py $TOKEN $DSPA_HOST



