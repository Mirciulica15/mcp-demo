import asyncio
import textwrap

from kubernetes import client, config

from mcp_server import mcp


@mcp.tool()
def get_pods_api() -> str:
    config.load_kube_config()
    v1 = client.CoreV1Api()
    print("Listing pods with their IPs:")
    ret = v1.list_pod_for_all_namespaces(watch=False)
    for i in ret.items:
        print("%s\t%s\t%s" % (i.status.pod_ip, i.metadata.namespace, i.metadata.name))
    return ret.items


@mcp.tool()
async def create_demo_nginx() -> str:
    """Create a demo Nginx Deployment+Service and return the direct access URL."""
    manifest_bytes = textwrap.dedent("""\
    apiVersion: apps/v1
    kind: Deployment
    metadata:
      name: nginx-demo
    spec:
      replicas: 1
      selector:
        matchLabels:
          app: nginx-demo
      template:
        metadata:
          labels:
            app: nginx-demo
        spec:
          containers:
          - name: nginx
            image: docker.io/library/nginx:latest
            imagePullPolicy: IfNotPresent
            ports:
            - containerPort: 80
    ---
    apiVersion: v1
    kind: Service
    metadata:
      name: nginx-demo
    spec:
      selector:
        app: nginx-demo
      type: LoadBalancer
      ports:
      - port: 8888
        targetPort: 80
    """).encode("utf-8")

    proc_apply = await asyncio.create_subprocess_exec(
        "kubectl", "apply", "-f", "-",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out_apply, err_apply = await proc_apply.communicate(manifest_bytes)
    if proc_apply.returncode != 0:
        return (
            f"Error applying manifest:\n"
            f"STDOUT: {out_apply.decode().strip()}\n"
            f"STDERR: {err_apply.decode().strip()}"
        )

    proc_rollout = await asyncio.create_subprocess_exec(
        "kubectl", "rollout", "status", "deployment/nginx-demo",
        "--timeout=60s",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    out_rollout, err_rollout = await proc_rollout.communicate()
    if proc_rollout.returncode != 0:
        return (
            f"Deployment rolled out with issues:\n"
            f"STDOUT: {out_rollout.decode().strip()}\n"
            f"STDERR: {err_rollout.decode().strip()}"
        )

    proc_sp = await asyncio.create_subprocess_exec(
        "kubectl", "get", "svc", "nginx-demo",
        "-o", "jsonpath={.spec.ports[0].port}",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    np_out, np_err = await proc_sp.communicate()
    if proc_sp.returncode != 0:
        return f"Deployed, but failed to get loadBalancer: {np_err.decode().strip()}"
    load_balancer = np_out.decode().strip()

    return f"Nginx demo is up! Access it at: http://localhost:{load_balancer}"
