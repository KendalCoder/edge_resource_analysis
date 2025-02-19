from kubernetes import client, config, watch, utils

class KubeClient():
    def __init__(self, logger):
        config.load_kube_config()
        self.client = client.ApiClient()
        self.v1 = client.CoreV1Api()
        self.logger = logger

    def create_cluster(self, hosts):
        hosts = self.config.hosts
        assert isinstance(hosts, list)
        self.logger.info("Creating nodes...")
        for host in hosts:
            template_path = os.path.join(self.current_file_path, f'template/{host.device}.yaml.tmpl')
            with open(template_path, "r") as file:
                t = Template(file.read())
                r = t.substitute({
                    "NAME": host.name.lower(),
                })
            node = yaml.safe_load(r)

            # Adding labels if exists
            if hasattr(host, "labels"):
                node_labels = node["metadata"]["labels"]
                node_labels.update(host.labels.__dict__)
                node["metadata"]["labels"] = node_labels

            # TODO: If the node exists an error occurs in the Kubernetes client.
            #       We ignore this for now but may want to update the node if exists.
            self.kube_client.create_object(node, ignore_error=True)

            device_model = devicemodel.device_to_model_mapping.get(host.device, None)
            self.nodes.append(device_model(node, self.kube_client))
            self.logger.info(f'Node {host.name} with the device type {host.device} is created')

    def create_new_workloads(self, workloads):
        # Sub-step: Create new workloads
        for pod in self.create_pods(events, steps):
            self.kube_client.create_object(pod)
            self.logger.info(f'Pod {pod["metadata"]["name"]} is created')

    
    def create_pods(self, workloads: dict, steps: int):
        template_path = os.path.join(self.current_file_path, "template/pod.yaml.tmpl")
        default = {
            "NAME": "mypod",
            "REQUEST_CPU": "100m",
            "REQUEST_MEMORY": "1Mi",
            "SCHEDULER": self.scheduler
        }
        for workload in workloads:
            d = default.copy()
            d.update(workload)
            d["NAME"] = f"{d['NAME']}-{steps}"
            with open(template_path, "r") as file:
                t = Template(file.read())
                r = t.substitute(d)
            pod = yaml.safe_load(r)
            yield pod

    def update_resource_use(self, pod, template_path="template/resource.yaml.tmpl"):
        """
        Update resource usage for a given pod. Create the usage object if not exists.

        Args:
            pod (dict): The pod specification.
            template_path (str): The path to the resource template file.
        """
        # Attempt to get the resource first if it exists
        resource_usage = self.kube_client.get_resourceusage_object(pod.metadata.name)
        if resource_usage is None:
            with open(os.path.join(self.current_file_path, template_path), "r") as file:
                t = Template(file.read())
                r = t.substitute({
                    "NAME": pod.metadata.name,
                    "CPU": pod.spec.containers[0].resources.requests["cpu"],
                    "MEMORY": pod.spec.containers[0].resources.requests["memory"],
                })
            resource_usage = yaml.safe_load(r)
            self.kube_client.update_resourceusage_object(pod.metadata.name, resource_usage)
        else:
            # Update the resource usage
            resource_usage["spec"]["cpu"] = pod.spec.containers[0].resources.requests["cpu"]
            resource_usage["spec"]["memory"] = pod.spec.containers[0].resources.requests["memory"]
            self.kube_client.update_resourceusage_object(pod.metadata.name, resource_usage)

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
    
    def cleanup(self):
        for pod in self.v1.list_namespaced_pod("default").items:
            self.v1.delete_namespaced_pod(pod.metadata.name, "default")
        return True

    def update(self, step):
        # TODO: Run update_resource_use() for running Pods in the nodes
        
        # for node in self.nodes:
        #     # TODO: Get information of the node from connected interface
        #     node_events = self.interface.get_node_info(node.name)

        #     # The node model updates the node state from the Kubernetes cluster
        #     node.update(node_events)
        pass