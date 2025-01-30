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

# Create the application object
cat <<EOF | oc apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: model-registry-${MODEL_REGISTRY_NAME}
  namespace: ${ARGOCD_NAMESPACE}
  annotations:
    argocd.argoproj.io/compare-options: IgnoreExtraneous
    argocd.argoproj.io/sync-options: SkipDryRunOnMissingResource=true
spec:
  project: default
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: ${NAMESPACE_NAME}
  source:
    path: gitops/model-registry
    repoURL: https://github.com/alpha-hack-program/model-serving-utils.git
    targetRevision: main
    helm:
      values: |
        registry:
          name: ${MODEL_REGISTRY_NAME}
        registryDb:
          databaseName: ${DATABASE_NAME}
          databaseUser: ${DATABASE_USER}
          databasePassword: ${DATABASE_PASSWORD}
  syncPolicy:
    automated:
      # prune: true
      selfHeal: true
EOF

