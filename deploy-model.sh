#!/bin/sh

# Error if no .env file is found
if [ ! -f .env ]; then
  echo "File .env not found. Use .env.example as a template"
  exit 1
fi

# Load .env file
set -a
. .env

# Check arguments, anableAuth is optional
# Arguments: [llama|granite] [8b] [3.0|3.1|3.2] <enableAuth>
if [ "$#" -lt 3 ]; then
  echo "Usage: $0 [llama|granite] [8b] [3.0|3.1|3.2] <enableAuth>"
  exit 1
fi

# If enableAuth is not provided, set it to false
if [ "$#" -eq 3 ]; then
  ENABLE_AUTH="false"
else
  # If the 4th argument is exactly enableAuth, set it to true, else fail and exit
  if [ "$4" = "enableAuth" ]; then
    ENABLE_AUTH="true"
  else
    echo "Usage: $0 [llama|granite] [8b] [3.0|3.1|3.2] <enableAuth>"
    exit 1
  fi
fi

# If file hf-creds.yaml doesn't exist, fail and exit
if [ ! -f hf-creds.yaml ]; then
  echo "File hf-creds.yaml not found"
  exit 1
fi

# Extract model family from the first argument
MODEL_FAMILY="$1"

# Extract model size from the second argument
MODEL_SIZE="$2"

# Extract model version from the third argument
MODEL_VERSION="$3"

# Compose model name with family, size and version
MODEL_NAME="${MODEL_FAMILY}-${MODEL_SIZE}-${MODEL_VERSION}"

# Ensure that MODEL_NAME is uri safe
MODEL_NAME=$(echo $MODEL_NAME | sed 's/[^a-zA-Z0-9-]/-/g' | sed 's/\./-/g')

# Compose namespace name
NAMESPACE_NAME="${MODEL_FAMILY}-${MODEL_SIZE}"

# If model family is granite, set the model.root to ibm-granite
if [ "$MODEL_FAMILY" = "granite" ]; then
  MODEL_ROOT="ibm-granite"
else
  MODEL_ROOT="meta-llama"
fi

# If model family is granite, set the model.id to family-version-size-instruct
if [ "$MODEL_FAMILY" = "granite" ]; then
  MODEL_ID="granite-${MODEL_VERSION}-${MODEL_SIZE}-instruct"
# else if model family is llama, model.id Llama-version-size-Instruct
elif [ "$MODEL_FAMILY" = "llama" ]; then
  MODEL_ID="Llama-${MODEL_VERSION}-${MODEL_SIZE}-Instruct"
else
  echo "Model family must be either llama or granite"
  exit 1
fi

echo "Deploying model ${MODEL_NAME} in namespace ${NAMESPACE_NAME}"
echo "Model Root: ${MODEL_ROOT}"
echo "Model ID: ${MODEL_ID}"

# If enableAuth is true, then create a service account named as the model name
if [ "$ENABLE_AUTH" = "true" ]; then
  oc create serviceaccount ${MODEL_NAME}-sa -n ${NAMESPACE_NAME}
fi

# Create the application object
cat <<EOF | oc apply -f -
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: ${MODEL_NAME}
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
    path: gitops/model
    repoURL: https://github.com/alpha-hack-program/model-serving-utils.git
    targetRevision: main
    helm:
      parameters:
        - name: argocdNamespace
          value: ${ARGOCD_NAMESPACE}
        - name: createNamespace # This has to be false if deploying in the an existing namespace
          value: 'true'
        - name: createSecret # This has to be false if the secret already exists
          value: 'false'
        - name: instanceName
          value: ${MODEL_NAME}
        - name: dataScienceProjectNamespace
          value: ${NAMESPACE_NAME}
        - name: dataScienceProjectDisplayName
          value: ${NAMESPACE_NAME}
        - name: model.root
          value: ${MODEL_ROOT}
        - name: model.id
          value: ${MODEL_ID}
        - name: model.name
          value: ${MODEL_NAME}
        - name: model.displayName
          value: "${MODEL_FAMILY} ${MODEL_SIZE} Instruct"
        - name: model.enableAuth
          value: "${ENABLE_AUTH}"
        - name: model.maxModelLen
          value: '4096'
        - name: model.runtime.displayName
          value: "vLLM ${MODEL_FAMILY} ${MODEL_SIZE} Instruct"
        - name: model.runtime.templateName
          value: "${MODEL_FAMILY}-${MODEL_SIZE}-serving-template"
        - name: model.accelerator.productName
          value: "NVIDIA-A10G"
        - name: model.accelerator.min
          value: '1'
        - name: model.accelerator.max
          value: '1'
        - name: model.connection.awsAccessKeyId
          value: ${AWS_S3_ACCESS_KEY}
        - name: model.connection.awsSecretAccessKey
          value: ${AWS_S3_SECRET_KEY}
        - name: model.connection.awsS3Bucket
          value: ${AWS_S3_BUCKET}
        - name: model.connection.awsS3Endpoint
          value: ${AWS_S3_ENDPOINT}
  syncPolicy:
    automated:
      # prune: true
      selfHeal: true
EOF

# Wait until the namespace is created
while [ "$(oc get namespace ${NAMESPACE_NAME} -o jsonpath='{.status.phase}')" != "Active" ]; do
  echo "Waiting for namespace ${NAMESPACE_NAME} to be created"
  sleep 5
done


# Apply hf-creds.yaml
oc create -f hf-creds.yaml -n ${NAMESPACE_NAME}