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
        self.workloads_total = 0
        self.current_step = 0

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

    def create_new_workloads(self, workloads, step):
        for workload in workloads:
            pod_template = create_pod(workload)
            # TODO: Set the scheduler name to avoid being scheduled by the default scheduler
            #   this is only for Kubernetes cluster
            pod_template["spec"]["schedulerName"] = "myscheduler"
            pod = SimpleWorkload(pod_template)
            # Pod name should be unique
            pod.name = f'{pod.name}-{step}'
            self.pending_pods[pod.name] = pod
            self.logger.info(f'Pod {pod.name} is created')
        self.workloads_total += len(workloads)

    def update(self, step):
        self.current_step = step
        for node_name, node in self.nodes.items():
            finished_pods = node.update(step, events=[])
            for p in finished_pods:
                self.logger.info(f'{p.name} is finished')
            self.nodes[node_name] = node
        # return finished_pods
    
    def placement(self, pod_name, node_name, step):
        pod = self.pending_pods.pop(pod_name, None)
        assert pod is not None
        node = self.nodes.get(node_name, None)
        assert node is not None
        node.place_pod(pod, step)
        self.logger.info(f'{pod.name} is placed on {node.name}')
        self.nodes[node.name] = node

    def cleanup(self):
        pass
