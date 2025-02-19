import os

from .devicemodel import devicemodel
from .cluster_utils import *
from .podmodel.simple_workload import SimpleWorkload

class TestCluster:
    def __init__(self, logger):
        self.logger = logger
        self.current_file_path = os.path.dirname(os.path.abspath(__file__))

        self.nodes = []
        self.pending_pods = []
        self.workloads_total = 0

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
            self.nodes.append(node)
            self.logger.info(f'Node {host.name} with the device type {host.device} is created')

    def create_new_workloads(self, workloads):
        for workload in workloads:
            pod_template = create_pod(workload)
            # TODO: Set the scheduler name to avoid being scheduled by the default scheduler
            #   this is only for Kubernetes cluster
            pod_template["spec"]["schedulerName"] = "myscheduler"
            pod = SimpleWorkload(pod_template)
            self.pending_pods.append(pod)
            self.logger.info(f'Pod {pod_template["metadata"]["name"]} is created')
        self.workloads_total += len(workloads)

    def update(self, step):
        for node in self.nodes:
            finished_pods = node.update(step, events=[])
            for p in finished_pods:
                self.logger.info(f'{p.name} is finished')
    
    def placement(self, pod_name, node_name, step):
        pod = next((p for p in self.pending_pods if p.name == pod_name), None)
        if pod:
            self.pending_pods.remove(pod)
        assert pod is not None
        node = next((n for n in self.nodes if n.name == node_name), None)
        assert node is not None
        node.place_pod(pod, step)
        self.logger.info(f'{pod.name} is placed on {node.name}')

    def cleanup(self):
        pass
