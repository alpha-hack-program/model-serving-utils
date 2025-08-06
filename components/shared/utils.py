from cProfile import label
from kubernetes import client as k8s_cli, config as k8s_conf

# Function that gets the model registry endpoint using a route object
def get_model_registry_endpoint(model_registry_name: str,
                                namespace: str) -> str:
    """
    Get the model registry endpoint from the route object in the specified namespace.
    Args:
        model_registry_name (str): Name of the model registry
        namespace (str): Namespace where the model registry route is located
    Returns:
        str: The model registry endpoint URL if found, otherwise None
    """
    print(f"Retrieving model registry endpoint for {model_registry_name} in namespace {namespace}")
    # Load in-cluster Kubernetes configuration but if it fails, load local configuration
    try:
        k8s_conf.load_incluster_config()
    except k8s_conf.config_exception.ConfigException:
        k8s_conf.load_kube_config()

    # Create Kubernetes API client
    api_instance = k8s_cli.CustomObjectsApi()

    # Selector to find the route by app label
    label_selector = f"app.kubernetes.io/name={model_registry_name}"
    print(f"Using label selector: {label_selector}")

    try:
        # Retrieve the route object
        routes = api_instance.list_namespaced_custom_object(
            group="route.openshift.io",
            version="v1",
            namespace=namespace,
            plural="routes",
            label_selector=label_selector
        )

        # Extract spec.host fields
        route_hosts = [route['spec']['host'] for route in routes['items']]
        print(f"Found route hosts: {route_hosts}")

        # Return the route host only if it contains "-http" else return None
        for route_host in route_hosts:
            if "-rest" in route_host:
                return f'https://{route_host}'
        return None
    
    except Exception as e:
        print(f"Error: {e}")
        return None