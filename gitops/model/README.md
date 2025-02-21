# Deploying Granite 8B

## Deploy the Application object in charge of deploying the Model

Adapt the following parameters to your environment:

- model.connection.scheme: http(s)
- name: model.connection.awsAccessKeyId: user to access the S3 server
- name: model.connection.awsSecretAccessKey: user key
- name: model.connection.awsDefaultRegion: region, none in MinIO
- name: model.connection.awsS3Bucket: bucket name
- name: model.connection.awsS3Endpoint: host and port (minio.ic-shared-minio.svc:9000)

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
        - name: argocdNamespace
          value: 'openshift-gitops'
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
          value: granite-3.1-8b-instruct
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
- name: model.connection.awsAccessKeyId: user to access the S3 server
- name: model.connection.awsSecretAccessKey: user key
- name: model.connection.awsDefaultRegion: region, none in MinIO
- name: model.connection.awsS3Bucket: bucket name
- name: model.connection.awsS3Endpoint: host and port (minio.ic-shared-minio.svc:9000)

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
    helm:
      parameters:
        - name: createNamespace # This has to be false if deploying in the an existing namespace
          value: 'true'
        - name: createSecret # This has to be false if the secret already exists
          value: 'false'
        - name: instanceName
          value: llama-3-8b
        - name: dataScienceProjectNamespace
          value: llama-3-8b # DATA_SCIENCE_PROJECT_NAMESPACE used later
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
    path: gitops/model
    repoURL: 'https://github.com/alpha-hack-program/doc-bot.git'
    targetRevision: main
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

# Deploying embeddings Nomic AI

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
  name: nomic-embed-text-v1
  namespace: openshift-gitops
  annotations:
    argocd.argoproj.io/compare-options: IgnoreExtraneous
    argocd.argoproj.io/sync-options: SkipDryRunOnMissingResource=true
spec:
  project: default
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: embeddings
  source:
    path: gitops/model
    repoURL: https://github.com/alpha-hack-program/model-serving-utils.git
    targetRevision: main
    helm:
      parameters:
        - name: argocdNamespace
          value: 'openshift-gitops'
        - name: createNamespace # This has to be false if deploying in the an existing namespace
          value: 'true'
        - name: createSecret # This has to be false if the secret already exists
          value: 'false'
        - name: instanceName
          value: "nomic"
        - name: dataScienceProjectNamespace
          value: "embeddings" # DATA_SCIENCE_PROJECT_NAMESPACE used later
        - name: dataScienceProjectDisplayName
          value: "embeddings"
        - name: model.root
          value: nomic-ai
        - name: model.id
          value: nomic-embed-text-v1
        - name: model.name
          value: nomic-embed-text-v1
        - name: model.displayName
          value: "Nomic Embed Text v1"
        # - name: model.maxModelLen
        #   value: '4096'
        - name: model.runtime.displayName
          value: "vLLM Runtime"
        - name: model.runtime.templateName
          value: "vllm-serving-template"
        # - name: model.accelerator.productName
        #   value: "NVIDIA-A10G"
        # - name: model.accelerator.min
        #   value: '1'
        # - name: model.accelerator.max
        #   value: '1'
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

# Deploying an embedding model

Supported models: https://docs.vllm.ai/en/latest/models/supported_models.html#text-embedding-task-embed

Model deployed https://huggingface.co/intfloat/multilingual-e5-large

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
  name: embeddings-gpu
  namespace: openshift-gitops
  annotations:
    argocd.argoproj.io/compare-options: IgnoreExtraneous
    argocd.argoproj.io/sync-options: SkipDryRunOnMissingResource=true
spec:
  project: default
  destination:
    server: 'https://kubernetes.default.svc'
    namespace: embeddings-gpu
  source:
    path: gitops/model
    repoURL: https://github.com/alpha-hack-program/model-serving-utils.git
    targetRevision: main
    helm:
      values: |
        dataScienceProjectDisplayName: embeddings-gpu
        dataScienceProjectNamespace: embeddings-gpu
        
        createNamespace: true

        instanceName: multilingual-e5-large

        model:
          root: intfloat
          id: multilingual-e5-large
          name: multilingual-e5-large-gpu
          displayName: multilingual-e5-large GPU
          maxReplicas: 1
          format: vLLM
          maxModelLen: '512'
          apiProtocol: REST
          embeddingsModel: true
          enableAuth: false
          rawDeployment: true
          runtime:
            templateName: vllm-serving-template
            templateDisplayName: vLLM Serving Template
            image: quay.io/modh/vllm:rhoai-2.17-cuda
            resources:
              limits:
                cpu: '8'
                memory: 24Gi
              requests:
                cpu: '6'
                memory: 24Gi
          accelerator:
            max: '1'
            min: '1'
            productName: NVIDIA-A10G
          connection:
            name: embeddings
            createSecret: true
            displayName: embeddings
            type: s3
            scheme: http
            awsAccessKeyId: minio
            awsSecretAccessKey: minio-parasol
            awsDefaultRegion: none
            awsS3Bucket: models
            awsS3Endpoint: minio.ic-shared-minio.svc:9000
          volumes:
            shm:
              sizeLimit: 2Gi
  syncPolicy:
    automated:
      # prune: true
      selfHeal: true
```

**Create a secret called hf-creds**

```sh
HF_USERNAME=xyz
HF_TOKEN=hf_**********
DATA_SCIENCE_PROJECT_NAMESPACE=embeddings-gpu

oc create secret generic hf-creds \
  --from-literal=HF_USERNAME=${HF_USERNAME} \
  --from-literal=HF_TOKEN=${HF_TOKEN} \
  -n ${DATA_SCIENCE_PROJECT_NAMESPACE}
```

## Tests

```sh
DATA_SCIENCE_PROJECT_NAMESPACE=embeddings-gpu
RUNTIME_MODEL_ID="multilingual-e5-large-gpu"
INFERENCE_URL=$(oc get inferenceservice/${RUNTIME_MODEL_ID} -n ${DATA_SCIENCE_PROJECT_NAMESPACE} -o jsonpath='{.status.url}')
INFERENCE_URL=$(oc get route/${RUNTIME_MODEL_ID} -n ${DATA_SCIENCE_PROJECT_NAMESPACE} -o jsonpath='{.spec.host}')
echo ${INFERENCE_URL}

curl -s -X 'POST' \
  "https://${INFERENCE_URL}/v1/embeddings" \
  -H "Content-Type: application/json" \
  -d '{ "model": "'${RUNTIME_MODEL_ID}'", "input": "Texto de ejemplo para embedding"}'
```

Big chunk of text...

```sh
time curl -s -X 'POST' \
  "https://${INFERENCE_URL}/v1/embeddings" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "model": "'${RUNTIME_MODEL_ID}'",
  "input": ["En un lugar de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho tiempo que vivía un hidalgo de los de lanza en astillero, adarga antigua, rocín flaco y galgo corredor. Una olla de algo más vaca que carnero, salpicón las más noches, duelos y quebrantos los sábados, lantejas los viernes, algún palomino de añadidura los domingos, consumían las tres partes de su hacienda. El resto della concluían sayo de velarte, calzas de velludo para las fiestas, con sus pantuflos de lo mesmo, y los días de entresemana se honraba con su vellorí de lo más fino. Tenía en su casa una ama que pasaba de los cuarenta, y una sobrina que no llegaba a los veinte, y un mozo de campo y plaza, que así ensillaba el rocín como tomaba la podadera. Frisaba la edad de nuestro hidalgo con los cincuenta años; era de complexión recia, seco de carnes, enjuto de rostro, gran madrugador y amigo de la caza. Quieren decir que tenía el sobrenombre de Quijada, o Quesada, que en esto hay alguna diferencia en los autores que deste caso escriben; aunque por conjeturas verosímiles se deja entender que se llamaba Quijana. Pero esto importa poco a nuestro cuento: basta que en la narración dél no se salga un punto de la verdad."]
}'
```

Loop 500 in 10s.

```sh
TEXT="En un lugar de la Mancha, de cuyo nombre no quiero acordarme, no ha mucho tiempo que vivía un hidalgo de los de lanza en astillero, adarga antigua, rocín flaco y galgo corredor. Una olla de algo más vaca que carnero, salpicón las más noches, duelos y quebrantos los sábados, lantejas los viernes, algún palomino de añadidura los domingos, consumían las tres partes de su hacienda. El resto della concluían sayo de velarte, calzas de velludo para las fiestas, con sus pantuflos de lo mesmo, y los días de entresemana se honraba con su vellorí de lo más fino. Tenía en su casa una ama que pasaba de los cuarenta, y una sobrina que no llegaba a los veinte, y un mozo de campo y plaza, que así ensillaba el rocín como tomaba la podadera. Frisaba la edad de nuestro hidalgo con los cincuenta años; era de complexión recia, seco de carnes, enjuto de rostro, gran madrugador y amigo de la caza. Quieren decir que tenía el sobrenombre de Quijada, o Quesada, que en esto hay alguna diferencia en los autores que deste caso escriben; aunque por conjeturas verosímiles se deja entender que se llamaba Quijana. Pero esto importa poco a nuestro cuento: basta que en la narración dél no se salga un punto de la verdad."

parallel_requests=10  # Number of parallel jobs

for i in {1..1500}
do
  echo "Request #$i"
  curl -s -X 'POST' "https://${INFERENCE_URL}/v1/embeddings" \
       -H 'accept: application/json' \
       -H 'Content-Type: application/json' \
       -d "$(jq -n --arg model "$RUNTIME_MODEL_ID" --arg text "$TEXT" '{model: $model, input: [$text]}')" &  # Run in background

  if (( i % parallel_requests == 0 )); then
    wait  # Wait for all background jobs to finish every 5 requests
  fi
done

wait  # Ensure any remaining jobs finish

```