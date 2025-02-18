import os

from .devicemodel import devicemodel
from .cluster_utils import *
from .podmodel.simple_workload import SimpleWorkload

class TestCluster:
    def __init__(self, logger):
        self.logger = logger
        self.current_file_path = os.path.dirname(os.path.abspath(__file__))

        self.nodes = {}
        self.pending_pods = {}

    def create_cluster(self, hosts):
        assert isinstance(hosts, list)
        self.logger.info("Creating nodes...")
        for host in hosts:
            node_template = create_node(host.name, host.device)

            # Adding labels if exists
            if hasattr(host, "labels"):
                node_labels = node_template["metadata"]["labels"]
                node_labels.update(host.labels.__dict__)
                node_template["metadata"]["labels"] = node_labels

            device_model_func = devicemodel.device_to_model_mapping.get(host.device, None)
            node = device_model_func(node_template)
            self.nodes[node.name] = node
            self.logger.info(f'Node {host.name} with the device type {host.device} is created')

    def create_new_workloads(self, workloads):
        for workload in workloads:
            pod_template = create_pod(workload)
            # TODO: Set the scheduler name to avoid being scheduled by the default scheduler
            #   this is only for Kubernetes cluster
            pod_template["spec"]["schedulerName"] = "myscheduler"
            pod = SimpleWorkload(pod_template)
            self.pending_pods[pod.name] = pod
            self.logger.info(f'Pod {pod_template["metadata"]["name"]} is created')

    def update(self, step):
        for node_name in self.nodes.keys():
            node = self.nodes.get(node_name)
            finished_pods = node.update(step, step, events=[])
            self.nodes[node_name] = node
            for p in finished_pods:
                self.logger.info(f'{p.name} is finished')
    
    def placement(self, pod_name, node_name, step):
        pod = self.pending_pods.pop(pod_name, None)
        assert pod is not None
        node = self.nodes.get(node_name)
        node.place_pod(pod, step)
        self.nodes[node_name] = node
        self.logger.info(f'{pod.name} is placed on {node.name}')
