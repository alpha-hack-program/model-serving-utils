import os
import yaml

from typing import Optional

import boto3
import botocore

from kubernetes import client as k8s_cli, config as k8s_conf
from kfp import client as kfp_cli

from kfp.dsl import Input, Metrics

aws_access_key_id = os.environ.get('AWS_ACCESS_KEY_ID')
aws_secret_access_key = os.environ.get('AWS_SECRET_ACCESS_KEY')
endpoint_url = os.environ.get('AWS_S3_ENDPOINT')
region_name = os.environ.get('AWS_DEFAULT_REGION')
bucket_name = os.environ.get('AWS_S3_BUCKET')
experiment_reports_folder = os.environ.get('EXPERIMENT_REPORTS_FOLDER_S3_KEY')

# Get token path from environment or default to kubernetes token location
TOKEN_PATH = os.environ.get("TOKEN_PATH", "/var/run/secrets/kubernetes.io/serviceaccount/token")

# Get the service account token or return None
def get_token():
    try:
        with open(TOKEN_PATH, "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error: {e}")
        return None
    
# Function that gets the model registry endpoint using a route object
def get_model_registry_endpoint(model_registry_name: str,
                                model_registry_namespace: str) -> str:
    # Load in-cluster Kubernetes configuration but if it fails, load local configuration
    try:
        k8s_conf.load_incluster_config()
    except k8s_conf.config_exception.ConfigException:
        k8s_conf.load_kube_config()

    # Create Kubernetes API client
    api_instance = k8s_cli.CustomObjectsApi()

    try:
        # Retrieve the route object
        route = api_instance.list_namespaced_custom_object(
            group="route.openshift.io",
            version="v1",
            namespace=model_registry_namespace,
            plural="routes",
            label_selector=f"app.kubernetes.io/instance={model_registry_name}"
        )

        # Extract spec.host field
        route_host = route['items'][0]['status']['ingress'][0]['host']

        # Return the route host only if it contains "-rest"
        if "-rest" in route_host:
            return route_host
        else:
            return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None

# Get the route host for the specified route name in the specified namespace
def get_route_host(route_name: str):
    # Load in-cluster Kubernetes configuration but if it fails, load local configuration
    try:
        k8s_conf.load_incluster_config()
    except k8s_conf.config_exception.ConfigException:
        k8s_conf.load_kube_config()

    # Get token path from environment or default to kubernetes token location
    NAMESPACE_PATH = os.environ.get("NAMESPACE_PATH", "/var/run/secrets/kubernetes.io/serviceaccount/namespace")

    # Get the current namespace
    with open(NAMESPACE_PATH, "r") as f:
        namespace = f.read().strip()

    print(f"namespace: {namespace}")

    # Create Kubernetes API client
    api_instance = k8s_cli.CustomObjectsApi()

    try:
        # Retrieve the route object
        route = api_instance.get_namespaced_custom_object(
            group="route.openshift.io",
            version="v1",
            namespace=namespace,
            plural="routes",
            name=route_name
        )

        # Extract spec.host field
        route_host = route['spec']['host']
        return route_host
    
    except Exception as e:
        print(f"Error: {e}")
        return None

# Get the service account token or return None
def get_token():
    try:
        with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as f:
            return f.read().strip()
    except Exception as e:
        print(f"Error: {e}")
        return None
    
# Function that generates a Dict from an Input[Metrics] object
def metrics_to_dict(metrics_input: Input[Metrics]) -> dict:
    # Iterate over the metrics and add them to the dictionary
    metrics_dict = {}
    for key, value in metrics_input.metadata():
        metrics_dict[key] = value

    return metrics_dict
        