from kubernetes import client, config, watch, utils

class KubeClient():
    def __init__(self, logger):
        config.load_kube_config()
        self.client = client.ApiClient()
        self.v1 = client.CoreV1Api()
        self.logger = logger

    def nodes_available(self):
        ready_nodes = []
        for n in self.v1.list_node().items:
                for status in n.status.conditions:
                    if status.status == "True" and status.type == "Ready":
                        ready_nodes.append(n)
        return ready_nodes
    
    def get_node(self, node_name):
        return self.v1.read_node(node_name)

    def get_fake_nodes(self):
        for n in self.v1.list_node().items:
            if n.metadata.annotations.get("kwok.x-k8s.io/node") == "fake":
                yield n

    def get_pods_on_node(self, node_name):
        return self.v1.list_namespaced_pod("default", field_selector=f"spec.nodeName={node_name}")

    def get_nodes_metrics(self):
        metrics_api = client.CustomObjectsApi()
        group = "metrics.k8s.io"
        version = "v1beta1"
        plural = "nodes"
        try:
            metrics = metrics_api.list_cluster_custom_object(
                group=group,
                version=version,
                plural=plural,
            )
            return metrics["items"]
        except client.exceptions.ApiException as e:
            self.logger.error(f'Failed to get metrics for nodes: {e}')
            return None

    def get_pods_metrics(self):
        metrics_api = client.CustomObjectsApi()
        group = "metrics.k8s.io"
        namespace = "default"
        version = "v1beta1"
        plural = "pods"
        try:
            metrics = metrics_api.list_namespaced_custom_object(
                group=group,
                version=version,
                plural=plural,
                namespace=namespace,
            )
            return metrics["items"]
        except client.exceptions.ApiException as e:
            self.logger.error(f'Failed to get metrics for nodes: {e}')
            return None

    def create_object(self, object_spec, ignore_error=False):
        try:
            return utils.create_from_dict(self.client, object_spec)
        except utils.FailToCreateError as ex:
            if ignore_error:
                return None
            else:
                raise ex

    def apply_custom_object(self, group, version, namespace, plural, name, body):
        custom_object_api = client.CustomObjectsApi()
        try:
            return custom_object_api.patch_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=name,
                body=body
            )
        except client.exceptions.ApiException as e:
            if e.status == 404:
                return custom_object_api.create_namespaced_custom_object(
                    group=group,
                    version=version,
                    namespace=namespace,
                    plural=plural,
                    body=body
                )
            else:
                raise e

    def get_custom_object(self, group, version, namespace, plural, name):
        custom_object_api = client.CustomObjectsApi()
        try:
            custom_object = custom_object_api.get_namespaced_custom_object(
                group=group,
                version=version,
                namespace=namespace,
                plural=plural,
                name=name
            )
            return custom_object
        except client.exceptions.ApiException as e:
            if e.status == 404:
                self.logger.error(f'Resource usage for pod {name} not found.')
                return None
            else:
                raise e

    def get_resourceusage_object(self, name):
        group = "kwok.x-k8s.io"
        version = "v1alpha1"
        namespace = "default"
        plural = "ResourceUsages".lower()
        return self.get_custom_object(group, version, namespace, plural, name)

    def update_resourceusage_object(self, name, body):
        group = "kwok.x-k8s.io"
        version = "v1alpha1"
        namespace = "default"
        plural = "ResourceUsages".lower()
        self.apply_custom_object(group, version, namespace, plural, name, body)
    
    def placement(self, pod_name, node_name, namespace="default"):
        target=client.V1ObjectReference()
        target.kind="Node"
        target.apiVersion="v1"
        target.name= node_name
        
        meta=client.V1ObjectMeta()
        meta.name=pod_name
        body=client.V1Binding(target=target)
        body.metadata=meta
        
        # In the Kubernetes Python client, it is known that
        # the below operation raises an exception even though
        # it succeeds the operation. For more information, see
        # https://github.com/kubernetes-client/python/issues/547
        try:
            res = self.v1.create_namespaced_binding(namespace, body)
        except:
            pass
        return True
    
    def delete_pods(self):
        for pod in self.v1.list_namespaced_pod("default").items:
            self.v1.delete_namespaced_pod(pod.metadata.name, "default")
        return True
