# DOCS: https://www.kubeflow.org/docs/components/pipelines/user-guides/components/ 

import os
import sys
import time

from kubernetes import client, config

import kfp

from kfp import compiler
from kfp import dsl
from kfp.dsl import Output, Metrics

from src.register_model import register_model

# Dummy component that generates metrics
@dsl.component(
    base_image="python:3.9",
    packages_to_install=["numpy==1.21.4"]
)
def generate_metrics(results_output_metrics: Output[Metrics]):
    results_output_metrics.log_metric("accuracy", 0.99)
    results_output_metrics.log_metric("precision", 0.95)

# This pipeline will download training dataset, download the model, test the model and if it performs well, 
# upload the model to another S3 bucket.
@dsl.pipeline(name="register-model-test-pl")
def pipeline(
    model_registry_name: str = "model-registry-dev",
    istio_system_namespace: str = "istio-system",
    model_name: str = "model_name",
    model_uri: str = "oci://model_uri",
    model_version: str = "0.1.0",
    model_description: str = "model_description",
    model_format_name: str = "onnx",
    model_format_version: str = "1",
    author: str = "author",
    owner: str = "owner",
    ):

    # Generate metrics
    generate_metrics_task = generate_metrics()

    # Generate labels
    labels = {
        "finance": "",
        "fraud": ""
    }

    # Register model
    register_model_task = register_model(
        model_registry_name=model_registry_name,
        istio_system_namespace=istio_system_namespace,
        model_name=model_name,
        model_uri=model_uri,
        model_version=model_version,
        model_description=model_description,
        model_format_name=model_format_name,
        model_format_version=model_format_version,
        author=author,
        owner=owner,
        labels=labels,
        input_metrics=generate_metrics_task.outputs["results_output_metrics"],
    ).set_caching_options(False)

    # register_model_task.set_service_account_name("register-model-sa")

if __name__ == '__main__':
    import time
    import sys
    import os

    from kfp import compiler

    from kubernetes import client, config

    def get_pipeline_by_name(client: kfp.Client, pipeline_name: str):
        import json

        # Define filter predicates
        filter_spec = json.dumps({
            "predicates": [{
                "key": "display_name",
                "operation": "EQUALS",
                "stringValue": pipeline_name,
            }]
        })

        # List pipelines with the specified filter
        pipelines = client.list_pipelines(filter=filter_spec)

        if not pipelines.pipelines:
            return None
        for pipeline in pipelines.pipelines:
            if pipeline.display_name == pipeline_name:
                return pipeline

        return None

    # Get the service account token or return None
    def get_token():
        try:
            with open("/var/run/secrets/kubernetes.io/serviceaccount/token", "r") as f:
                return f.read().strip()
        except Exception as e:
            print(f"Error: {e}")
            return None

    # Get the route host for the specified route name in the specified namespace
    def get_route_host(route_name: str):
        # Load in-cluster Kubernetes configuration but if it fails, load local configuration
        try:
            config.load_incluster_config()
        except config.config_exception.ConfigException:
            config.load_kube_config()

        # Get the current namespace
        with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace", "r") as f:
            namespace = f.read().strip()

        # Create Kubernetes API client
        api_instance = client.CustomObjectsApi()

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
    
    pipeline_package_path = __file__.replace('.py', '.yaml')

    compiler.Compiler().compile(
        pipeline_func=pipeline,
        package_path=pipeline_package_path
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

    # Pipeline name
    pipeline_name = os.path.basename(__file__).replace('.py', '')

    # If both kfp_endpoint and token are provided, upload the pipeline
    if kfp_endpoint and token:
        client = kfp.Client(host=kfp_endpoint, existing_token=token)

        # If endpoint doesn't have a protocol (http or https), add https
        if not kfp_endpoint.startswith("http"):
            kfp_endpoint = f"https://{kfp_endpoint}"

        try:
            # Get the pipeline by name
            print(f"Pipeline name: {pipeline_name}")
            existing_pipeline = get_pipeline_by_name(client, pipeline_name)
            if existing_pipeline:
                print(f"Pipeline {existing_pipeline.pipeline_id} already exists. Uploading a new version.")
                # Upload a new version of the pipeline with a version name equal to the pipeline package path plus a timestamp
                pipeline_version_name=f"{pipeline_name}-{int(time.time())}"
                client.upload_pipeline_version(
                    pipeline_package_path=pipeline_package_path,
                    pipeline_id=existing_pipeline.pipeline_id,
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