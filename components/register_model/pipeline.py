# DOCS: https://www.kubeflow.org/docs/components/pipelines/user-guides/components/ 

import os

from kfp import dsl
from kfp.dsl import Output, Metrics

from src.register_model import register_model

COMPONENT_NAME=os.getenv("COMPONENT_NAME")
print(f"COMPONENT_NAME: {COMPONENT_NAME}")

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
    model_registry_namespace: str = "rhoai-model-registries",
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
    generate_metrics_task = generate_metrics() # type: ignore

    # Generate labels
    labels = """{
        "finance": "",
        "fraud": ""
    }"""

    # Register model
    register_model_task = register_model(
        model_registry_name=model_registry_name,
        model_registry_namespace=model_registry_namespace,
        model_name=model_name,
        model_uri=model_uri,
        model_version=model_version,
        model_description=model_description,
        model_format_name=model_format_name,
        model_format_version=model_format_version,
        author=author,
        owner=owner,
        labels=labels
    ).set_caching_options(False)

    # register_model_task.set_service_account_name("register-model-sa")

if __name__ == '__main__':
    from shared.kubeflow import compile_and_upsert_pipeline
    
    import os

    pipeline_package_path = __file__.replace('.py', '.yaml')

    # Pipeline name
    pipeline_name=f"{COMPONENT_NAME}_pl"

    compile_and_upsert_pipeline(
        pipeline_func=pipeline,
        pipeline_package_path=pipeline_package_path,
        pipeline_name=pipeline_name
    )