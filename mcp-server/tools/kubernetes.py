from kubernetes import client, config
from kubernetes.client import V1Pod, V1Service

from mcp_server import mcp


def get_client_api() -> client.CoreV1Api:
    """Get Kubernetes API client."""
    config.load_kube_config()
    return client.CoreV1Api()


@mcp.tool()
def get_pods_api() -> str:
    v1 = get_client_api()
    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
    return ret.items


@mcp.tool()
def create_demo_nginx() -> str:
    """Create a demo Nginx Deployment+Service and return the direct access URL."""
    v1 = get_client_api()
    pod: V1Pod = V1Pod(
        api_version="v1",
        kind="Pod",
        metadata={"name": "nginx-demo"},
        spec={
            "containers": [
                {
                    "name": "nginx",
                    "image": "docker.io/library/nginx:latest",
                    "imagePullPolicy": "IfNotPresent",
                    "ports": [{"containerPort": 80}],
                }
            ]
        },
    )
    v1.create_namespaced_pod("default", pod)
    service: V1Service = V1Service(
        api_version="v1",
        kind="Service",
        metadata={"name": "nginx-demo"},
        spec={
            "type": "LoadBalancer",
            "ports": [{"port": 80, "targetPort": 80}],
            "selector": {"app": "nginx-demo"},
        },
    )
    v1.create_namespaced_service("default", service)

    return f"Nginx demo is up!"
