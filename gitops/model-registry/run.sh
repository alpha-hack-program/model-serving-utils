#!/bin/sh
ARGOCD_APP_NAME=model-registry

# Load environment variables
DATA_SCIENCE_PROJECT_NAMESPACE="model-registry"

helm template . --name-template ${ARGOCD_APP_NAME} \
  --set registryDb.databaseName="metadb" \
  --set registryDb.databaseUser="root" \
  --set registryDb.databasePassword="test" \
  --include-crds