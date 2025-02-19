# Deploying a Model Registry

## Deploy the Application object in charge of deploying the Model Registry

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
```

## Test

```sh
MODEL_REGISTRY_URL=https://model-registry-users-rhoai-model-registries.apps.cluster-cwxrr.cwxrr.sandbox1533.opentlc.com
RUNTIME_MODEL_ID=$(curl -ks -X 'GET' "${MODEL_REGISTRY_URL}/v1/models" -H 'accept: application/json' | jq -r .data[0].id )
echo ${RUNTIME_MODEL_ID}

curl -s -X 'POST' \
  "${MODEL_REGISTRY_URL}/v1/completions" \
  -H 'accept: application/json' \
  -H 'Content-Type: application/json' \
  -d '{
  "model": "'${RUNTIME_MODEL_ID}'",
  "prompt": "San Francisco is a",
  "max_tokens": 25,
  "temperature": 0
}'
```

