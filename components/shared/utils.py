from kubernetes import client as k8s_cli, config as k8s_conf


def get_model_registry_endpoint(model_registry_name: str, namespace: str) -> str | None:
    """
    Get the model registry REST endpoint from the route in the specified namespace.

    Uses label selectors matching OpenShift AI / ODH model registry operator patterns:
    - app.kubernetes.io/name={name} (ModelRegistry CR name)
    - app.kubernetes.io/instance={name} or {name}-http or {name}-users (route variants)

    Args:
        model_registry_name: Name of the model registry (e.g. model-registry-dev)
        namespace: Namespace where the model registry is located (e.g. rhoai-model-registries)

    Returns:
        The model registry endpoint URL (http:// or https://) if found, otherwise None.
    """
    try:
        k8s_conf.load_incluster_config()
    except k8s_conf.config_exception.ConfigException:
        k8s_conf.load_kube_config()

    api = k8s_cli.CustomObjectsApi()
    label_namespace_pairs = [
        (f"app.kubernetes.io/name={model_registry_name}", namespace),
        (f"app.kubernetes.io/instance={model_registry_name}", namespace),
        (f"app.kubernetes.io/instance={model_registry_name}-http", namespace),
        (f"app.kubernetes.io/instance={model_registry_name}-users", namespace),
        (f"app.kubernetes.io/instance={model_registry_name}", "istio-system"),
        (f"app.kubernetes.io/instance={model_registry_name}-users", "istio-system"),
    ]

    for label_selector, ns in label_namespace_pairs:
        try:
            routes = api.list_namespaced_custom_object(
                group="route.openshift.io",
                version="v1",
                namespace=ns,
                plural="routes",
                label_selector=label_selector,
            )
            for route in routes.get("items", []):
                host = route.get("spec", {}).get("host", "")
                if "-rest" in host or "-http" in host:
                    scheme = "https" if route.get("spec", {}).get("tls") else "http"
                    return f"{scheme}://{host}"
        except Exception:
            continue

    return None