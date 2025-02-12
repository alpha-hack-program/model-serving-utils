# Model Registry Examples

## Prepare environment

Let's get the host of the model registry by using an `oc` command.

```sh
MODEL_REGISTRY_NAME=model-registry-dev
MODEL_REGISTRY_HOST=$(oc get routes -n istio-system -l app.kubernetes.io/instance=${MODEL_REGISTRY_NAME} -o json | jq '.items[].status.ingress[].host | select(contains("-rest"))')
TOKEN=$(oc whoami -t)
```

## Get All Registered Models

```sh
curl -sX 'GET' "https://${MODEL_REGISTRY_HOST}/api/model_registry/v1alpha3/registered_models?pageSize=100&orderBy=ID&sortOrder=DESC" \
  -H "accept: application/json" -H "Authorization: Bearer ${TOKEN}" | jq .
```

Output:

```json
{
  "items": [
    {
      "createTimeSinceEpoch": "1738605918818",
      "customProperties": {
        "finance": {
          "metadataType": "MetadataStringValue",
          "string_value": ""
        },
        "production": {
          "metadataType": "MetadataStringValue",
          "string_value": ""
        }
      },
      "id": "3",
      "lastUpdateTimeSinceEpoch": "1738605926153",
      "name": "mnist",
      "owner": "admin",
      "state": "LIVE"
    }
  ],
  "nextPageToken": "",
  "pageSize": 100,
  "size": 3
}
```

## Get a Registered Model by name or id

```sh
MODEL_NAME="test"
MODEL_ID=5
```

Name and externalId:

```sh
curl -sX 'GET' "https://${MODEL_REGISTRY_HOST}/api/model_registry/v1alpha3/registered_model?name=${MODEL_NAME}&externalId=${MODEL_ID}" \
  -H "accept: application/json" \
  -H "Authorization: Bearer ${TOKEN}"
```

Output:

```json
{"createTimeSinceEpoch":"1738917532453","customProperties":{},"description":"desc","id":"5","lastUpdateTimeSinceEpoch":"1738917532453","name":"test","owner":"admin","state":"LIVE"}
```

Name:

```sh
curl -X 'GET' "https://${MODEL_REGISTRY_HOST}/api/model_registry/v1alpha3/registered_model?name=${MODEL_NAME}' \
  -H "accept: application/json" -H "Authorization: Bearer ${TOKEN}"
```

Output:

```json
{"createTimeSinceEpoch":"1738917532453","customProperties":{},"description":"desc","id":"5","lastUpdateTimeSinceEpoch":"1738917532453","name":"test","owner":"admin","state":"LIVE"}
```

By id:

```sh
curl -X 'GET' "https://${MODEL_REGISTRY_HOST}/api/model_registry/v1alpha3/registered_models/${MODEL_ID}' \
  -H "accept: application/json" \
  -H "Authorization: Bearer ${TOKEN}"
```

Output:

```json
{
  "createTimeSinceEpoch": "1738917532453",
  "customProperties": {},
  "description": "desc",
  "id": "5",
  "lastUpdateTimeSinceEpoch": "1738917532453",
  "name": "test",
  "owner": "admin",
  "state": "LIVE"
}
```

## Get a versions of a registered model

> TODO! Here name may not be the model name but the version name... and it's an or not and...

```sh
curl -sX 'GET' "https://${MODEL_REGISTRY_HOST}/api/model_registry/v1alpha3/registered_models/${MODEL_ID}/versions?name=${MODEL_NAME}&pageSize=100&orderBy=ID&sortOrder=DESC' \ 
 -H "accept: application/json"   -H "Authorization: Bearer ${TOKEN}" | jq .
```

```json
{
  "items": [
    {
      "author": "admin",
      "createTimeSinceEpoch": "1738917642516",
      "customProperties": {},
      "id": "8",
      "lastUpdateTimeSinceEpoch": "1738917642516",
      "name": "1.02_dev",
      "registeredModelId": "5",
      "state": "LIVE"
    },
    {
      "author": "admin",
      "createTimeSinceEpoch": "1738917581294",
      "customProperties": {},
      "id": "7",
      "lastUpdateTimeSinceEpoch": "1738917581294",
      "name": "1.01_dev",
      "registeredModelId": "5",
      "state": "LIVE"
    },
    {
      "author": "admin",
      "createTimeSinceEpoch": "1738917532646",
      "customProperties": {},
      "id": "6",
      "lastUpdateTimeSinceEpoch": "1738917532646",
      "name": "1.00_dev",
      "registeredModelId": "5",
      "state": "LIVE"
    }
  ],
  "nextPageToken": "",
  "pageSize": 100,
  "size": 3
}
```

## Get artifacts of a versions of a registered model

```sh
MODEL_VERSION_ID=8
```

```sh
curl -sX 'GET'  "https://${MODEL_REGISTRY_HOST}/api/model_registry/v1alpha3/model_versions/${MODEL_VERSION_ID}/artifacts?externalId=${MODEL_ID}&pageSize=100&orderBy=ID&sortOrder=DESC'  \
  -H "accept: application/json" -H "Authorization: Bearer ${TOKEN}" | jq .
```

Output:

```json
{
  "items": [
    {
      "artifactType": "model-artifact",
      "createTimeSinceEpoch": "1738917642757",
      "customProperties": {},
      "id": "5",
      "lastUpdateTimeSinceEpoch": "1738917642757",
      "modelFormatName": "safetensors",
      "name": "1.02_dev",
      "state": "LIVE",
      "uri": "s3://models/models/yolo_1.002?endpoint=http%3A%2F%2Fminio.ic-shared-minio.svc%3A9000&defaultRegion=none"
    }
  ],
  "nextPageToken": "",
  "pageSize": 100,
  "size": 1
}
```

Another example:

```sh
curl -sX 'GET' "https://${MODEL_REGISTRY_HOST}/api/model_registry/v1alpha3/model_versions/${MODEL_VERSION_ID}/artifacts?externalId=${MODEL_ID}&pageSize=100&orderBy=ID&sortOrder=DESC' \
  -H "accept: application/json" -H "Authorization: Bearer ${TOKEN}" | jq . 
```

Output:

```json
{
  "items": [
    {
      "artifactType": "model-artifact",
      "createTimeSinceEpoch": "1739117831049",
      "customProperties": {},
      "id": "10",
      "lastUpdateTimeSinceEpoch": "1739117831049",
      "modelFormatName": "onnx",
      "modelFormatVersion": "1",
      "name": "model_name",
      "state": "UNKNOWN",
      "uri": "oci://model_uri"
    }
  ],
  "nextPageToken": "",
  "pageSize": 100,
  "size": 1
}
```

