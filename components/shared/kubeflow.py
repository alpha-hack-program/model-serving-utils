import os
import time
import sys

from typing import Optional

from kubernetes import client as k8s_cli, config as k8s_conf

import kfp
from kfp import client as kfp_cli, compiler
from kfp.dsl import base_component

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

def get_pipeline_id_by_name(client: kfp_cli.Client, pipeline_name: str):
    return client.get_pipeline_id(pipeline_name)

def get_pipeline(client: kfp_cli.Client, pipeline_id: str):
    return client.get_pipeline(pipeline_id)

def get_latest_pipeline_version_id(client: kfp_cli.Client, pipeline_id: str) -> Optional[str]:
    pipeline_versions = client.list_pipeline_versions(
        pipeline_id=pipeline_id,
        sort_by="created_at desc",
        page_size=10
    )
    if pipeline_versions and len(pipeline_versions.pipeline_versions) >= 1:
        # Order pipeline_versions by created_at in descending order and return the first one
        pipeline_versions.pipeline_versions.sort(key=lambda x: x.created_at, reverse=True)
        return pipeline_versions.pipeline_versions[0].pipeline_version_id
    else:
        return None

# Function that create a kpf experiment and returns the id
def create_experiment(client: kfp_cli.Client, experiment_name: str) -> str:
    experimment = client.create_experiment(name=experiment_name)
    print(f">>>experimment: {experimment}")
    return experimment.experiment_id

# Function that creates a run of a pipeline id in a given experiment id with the latest version of the pipeline
def create_run(client: kfp_cli.Client, pipeline_id: str, experiment_id: str, run_name: str, params: dict) -> str:
    pipeline_version_id = get_latest_pipeline_version_id(client, pipeline_id)
    print(f">>>pipeline_version_id: {pipeline_version_id}")
    if pipeline_version_id is None:
        raise ValueError(f"No pipeline versions found for pipeline_id: {pipeline_id}")
    run = client.run_pipeline(
        experiment_id=experiment_id,
        job_name=run_name,
        pipeline_id=pipeline_id,
        version_id=pipeline_version_id,
        params=params
    )
    print(f"run: {run}")
    return run.run_id

# Function that compiles and upserts a pipeline
def compile_and_upsert_pipeline(
        pipeline_func: base_component.BaseComponent,
        pipeline_package_path: str,
        pipeline_name: str) -> str:
    
    # Compile the pipeline
    compiler.Compiler().compile(
        pipeline_func=pipeline_func,
        package_path=pipeline_package_path,
    )

    # Take token and kfp_endpoint as optional command-line arguments
    token = sys.argv[1] if len(sys.argv) > 1 else None
    kfp_endpoint = sys.argv[2] if len(sys.argv) > 2 else None

    if not token:
        print("Token endpoint not provided finding it automatically.")
        token = get_token()

    if not kfp_endpoint:
        print("KFP endpoint not provided finding it automatically.")
        kfp_endpoint = get_route_host(route_name="ds-pipeline-dspa")

    # If both kfp_endpoint and token are provided, upload the pipeline
    if kfp_endpoint and token:
        client = kfp.Client(host=kfp_endpoint, existing_token=token)

        # If endpoint doesn't have a protocol (http or https), add https
        if not kfp_endpoint.startswith("http"):
            kfp_endpoint = f"https://{kfp_endpoint}"

        try:
            # Get the pipeline by name
            print(f"Pipeline name: {pipeline_name}")
            pipeline_id = get_pipeline_id_by_name(client, pipeline_name)
            if pipeline_id:
                print(f"Pipeline {pipeline_id} already exists. Uploading a new version.")
                # Upload a new version of the pipeline with a version name equal to the pipeline package path plus a timestamp
                pipeline_version_name=f"{pipeline_name}-{int(time.time())}"
                client.upload_pipeline_version(
                    pipeline_package_path=pipeline_package_path,
                    pipeline_id=pipeline_id,
                    pipeline_version_name=pipeline_version_name
                )
                print(f"Pipeline version uploaded successfully to {kfp_endpoint}")
            else:
                print(f"Pipeline {pipeline_name} does not exist. Uploading a new pipeline.")
                print(f"Pipeline package path: {pipeline_package_path}")
                # Upload the compiled pipeline
                client.upload_pipeline(
                    pipeline_package_path=pipeline_package_path,
                    pipeline_name=pipeline_name
                )
                print(f"Pipeline uploaded successfully to {kfp_endpoint}")
        except Exception as e:
            print(f"Failed to upload the pipeline: {e}")
    else:
        print("KFP endpoint or token not provided. Skipping pipeline upload.")

