# Deploying Granite 8B

## Deploy the Application object in charge of deploying the Model

Adapt the following parameters to your environment:

- model.connection.scheme: http(s)
- model.connection.awsAccessKeyId: user to access the S3 server
- model.connection.awsSecretAccessKey: user key
- model.connection.awsDefaultRegion: region, none in MinIO
- model.connection.awsS3Bucket: bucket name
- model.connection.awsS3Endpoint: host and port (minio.ic-shared-minio.svc:9000)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: granite-8b
  namespace: openshift-gitops
  annotations:
    argocd.argoproj.io/compare-options: IgnoreExtraneous
    argocd.argoproj.io/sync-options: SkipDryRunOnMissingResource=true
spec:
  project: default
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: granite-8b # DATA_SCIENCE_PROJECT_NAMESPACE used later
  source:
    path: gitops/model
    repoURL: https://github.com/alpha-hack-program/model-serving-utils.git
    targetRevision: main
    helm:
      parameters:
        - name: createNamespace # This has to be false if deploying in the an existing namespace
          value: 'true'
        - name: createSecret # This has to be false if the secret already exists
          value: 'false'
        - name: instanceName
          value: "granite-8b"
        - name: dataScienceProjectNamespace
          value: "granite-8b" # DATA_SCIENCE_PROJECT_NAMESPACE used later
        - name: dataScienceProjectDisplayName
          value: "granite-8b"
        - name: model.root
          value: ibm-granite
        - name: model.id
          value: granite-8b-code-instruct
        - name: model.name
          value: granite-8b
        - name: model.displayName
          value: "Granite 8B Code Instruct"
        - name: model.maxModelLen
          value: '4096'
        - name: model.runtime.displayName
          value: "vLLM Granite 3 8B"
        - name: model.runtime.templateName
          value: "granite-8b-serving-template"
        - name: model.accelerator.productName
          value: "NVIDIA-A10G"
        - name: model.accelerator.min
          value: '1'
        - name: model.accelerator.max
          value: '1'
  syncPolicy:
    automated:
      # prune: true
      selfHeal: true
```
## Create a secret called hf-creds in the namespace ${DATA_SCIENCE_PROJECT_NAMESPACE}

```sh
HF_USERNAME=xyz
HF_TOKEN=hf_**********
DATA_SCIENCE_PROJECT_NAMESPACE=granite-8b

oc create secret generic hf-creds \
  --from-literal=HF_USERNAME=${HF_USERNAME} \
  --from-literal=HF_TOKEN=${HF_TOKEN} \
  -n ${DATA_SCIENCE_PROJECT_NAMESPACE}
```

## Test

```sh
INFERENCE_URL=$(oc get inferenceservice/granite-8b -n granite-8b -o jsonpath='{.status.url}')
RUNTIME_MODEL_ID=$(curl -ks -X 'GET' "${INFERENCE_URL}/v1/models" -H 'accept: application/json' | jq -r .data[0].id )
echo ${RUNTIME_MODEL_ID}

curl -s -X 'POST' \
  "${INFERENCE_URL}/v1/completions" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "model": "'${RUNTIME_MODEL_ID}'",
  "prompt": "San Francisco is a",
  "max_tokens": 25,
  "temperature": 0
}'
```

# Llama 3 8B

## Deploy the Application object in charge of deploying the Model

Adapt the following parameters to your environment:

- model.connection.scheme: http(s)
- model.connection.awsAccessKeyId: user to access the S3 server
- model.connection.awsSecretAccessKey: user key
- model.connection.awsDefaultRegion: region, none in MinIO
- model.connection.awsS3Bucket: bucket name
- model.connection.awsS3Endpoint: host and port (minio.ic-shared-minio.svc:9000)

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: llama-3-8b
  namespace: openshift-gitops
  annotations:
    argocd.argoproj.io/compare-options: IgnoreExtraneous
    argocd.argoproj.io/sync-options: SkipDryRunOnMissingResource=true
spec:
  destination:
    namespace: llama-3-8b # DATA_SCIENCE_PROJECT_NAMESPACE used later
    server: 'https://kubernetes.default.svc'
  project: default
  source:
    path: gitops/model
    repoURL: https://github.com/alpha-hack-program/model-serving-utils.git
    targetRevision: main
    helm:
      parameters:
        - name: createNamespace # This has to be false if deploying in the an existing namespace
          value: 'true'
        - name: createSecret # This has to be false if the secret already exists
          value: 'false'
        - name: instanceName
          value: llama-3-8b
        - name: dataScienceProjectNamespace
          value: llama-3-8b
        - name: dataScienceProjectDisplayName
          value: Project llama-3-8b
        - name: model.root
          value: mistralai
        - name: model.id
          value: Mistral-7B-Instruct-v0.2
        - name: model.name
          value: llama-3-8b
        - name: model.displayName
          value: Llama 8B
        - name: model.accelerator.productName
          value: NVIDIA-A10G
        - name: model.accelerator.min
          value: '1'
        - name: model.accelerator.max
          value: '1'
        - name: model.connection.name
          value: llm
        - name: model.connection.displayName
          value: llm
        - name: model.connection.type
          value: s3
        - name: model.connection.scheme
          value: http
        - name: model.connection.awsAccessKeyId
          value: minio
        - name: model.connection.awsSecretAccessKey
          value: minio123
        - name: model.connection.awsDefaultRegion
          value: none
        - name: model.connection.awsS3Bucket
          value: models
        - name: model.connection.awsS3Endpoint
          value: 'minio.ic-shared-minio.svc:9000'
  syncPolicy:
    automated:
      selfHeal: true
```

## Create a secret called hf-creds in the namespace ${DATA_SCIENCE_PROJECT_NAMESPACE}

```sh
HF_USERNAME=xyz
HF_TOKEN=hf_**********
DATA_SCIENCE_PROJECT_NAMESPACE=llama-3-8b

oc create secret generic hf-creds \
  --from-literal=HF_USERNAME=${HF_USERNAME} \
  --from-literal=HF_TOKEN=${HF_TOKEN} \
  -n ${DATA_SCIENCE_PROJECT_NAMESPACE}
```

## Test

```sh
INFERENCE_URL=$(oc get inferenceservice/llama-3-8b -n llama-3-8b -o jsonpath='{.status.url}')
RUNTIME_MODEL_ID=$(curl -ks -X 'GET' "${INFERENCE_URL}/v1/models" -H 'accept: application/json' | jq -r .data[0].id )
echo ${RUNTIME_MODEL_ID}

curl -s -X 'POST' \
  "${INFERENCE_URL}/v1/completions" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "model": "'${RUNTIME_MODEL_ID}'",
  "prompt": "San Francisco is a",
  "max_tokens": 25,
  "temperature": 0
}'
```