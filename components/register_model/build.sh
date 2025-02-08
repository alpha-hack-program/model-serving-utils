#!/bin/sh

. .env

kfp component build src/ --component-filepattern ${COMPONENT_NAME}.py --no-push-image --overwrite-dockerfile --no-build-image

podman build -t ${COMPONENT_NAME}:latest -f src/Dockerfile src/
