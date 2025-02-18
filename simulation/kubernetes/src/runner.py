import os
from string import Template
import importlib
import time

from .kubeclient import KubeClient
from .envconfig import EnvConfig
from .utils import *
from .devicemodel import devicemodel

import yaml
from tqdm import tqdm

class Runner():
    """
        Runner manages the flow of simulation.
    """
    def __init__(self, config: dict, logger):
        self.config = EnvConfig(**config)
        self.kube_client = KubeClient(logger)
        self.logger = logger
        self.total_steps = config.get("steps", 20)
        self.nodes = []
        self.current_file_path = os.path.dirname(os.path.abspath(__file__))

        # Module loading fails without adding the src directory to the path
        import sys
        sys.path.append("src")

        scheduler_name = self.config.scheduler
        self.logger.info(f'Loading the scheduler {scheduler_name}')
        try:
            scheduler_module = importlib.import_module(f'scheduler.{scheduler_name.lower()}')
            scheduler_class = getattr(scheduler_module, scheduler_name)
        except ModuleNotFoundError as ex:
            self.logger.error(f'{scheduler_name} is not found in the scheduler directory: {ex}')
            raise ex
        self.scheduler = scheduler_class()

        dataloader_name = self.config.dataloader
        self.logger.info(f'Loading the dataloader {dataloader_name}')
        try:
            dataloader_module = importlib.import_module(f'dataloader.{dataloader_name.lower()}')
            dataloader_class = getattr(dataloader_module, dataloader_name)
        except ModuleNotFoundError as ex:
            self.logger.error(f'{dataloader_name} is not found in the scheduler directory: {ex}')
            raise ex
        self.dataloader = dataloader_class()

        visualization_name = self.config.visualization
        self.logger.info(f'Loading the visualization {visualization_name}')
        try:
            visualization_module = importlib.import_module(f'visualization.{visualization_name.lower()}')
            visualization_class = getattr(visualization_module, visualization_name)
        except ModuleNotFoundError as ex:
            self.logger.error(f'{visualization_name} is not found in the scheduler directory: {ex}')
            raise ex
        self.visualization = visualization_class()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def create_cluster(self):
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

    def cleanup(self):
        self.kube_client.delete_pods()
        self.visualization.finish()

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

    def update_pods_on_fake_nodes(self):
        fake_nodes = list(self.kube_client.get_fake_nodes())
        for node in fake_nodes:
            pods = self.kube_client.v1.list_namespaced_pod("default", field_selector=f"spec.nodeName={node.metadata.name}")
            for pod in pods.items:
                self.update_resource_use(pod)

    def aggregate_metrics(self):
        """
        Aggregate metrics from the simuation.
        """
        metrics = {}
        # TODO: The Kubernetes metrics server needs some time to update its metrics
        #       which slows down the simulation because the simulation waits for the metrics.
        #       We will use explicit resource usage specified by workloads until we find
        #       a better solution to collect metrics while the simulation is running.
        # for node_metric in self.kube_client.get_nodes_metrics():
        #     self.logger.info(f"Node metrics: {node_metric}")
        #     metrics.update({
        #         f'node_{node_metric["metadata"]["name"]}_cpu': convert_to_millicores(node_metric['usage']['cpu']),
        #         f'node_{node_metric["metadata"]["name"]}_memory': convert_to_bytes(node_metric['usage']['memory'])
        #     })
        # for pod_metric in self.kube_client.get_pods_metrics():
        #     self.logger.info(f"Pod metrics: {pod_metric}")
        #     metrics.update({
        #         f'pod_{pod_metric["metadata"]["name"]}_cpu': convert_to_millicores(pod_metric["containers"][0]['usage']['cpu']),
        #         f'pod_{pod_metric["metadata"]["name"]}_memory': convert_to_bytes(pod_metric["containers"][0]['usage']['memory'])
        #     })

        # Add node metrics from the device model
        for node in self.nodes:
            for metric_name, metric_value in node.get_node_metrics():
                metrics[f"node_{node}_{metric_name}"] = metric_value
        return metrics

    def calculate_scores(self):
        """
        Calculate scores for the simulation.
        """
        scores = {}
        nodes = self.kube_client.nodes_available()
        pods = self.kube_client.v1.list_namespaced_pod("default").items

        # TODO: We need to implement a scoring mechanism for the simulation.
        #       Scores may include node power consumption, fairness, and other metrics.
        running_pods = [pod for pod in pods if pod.status.phase == "Running"]
        pending_pods = [pod for pod in pods if pod.status.phase == "Pending"]

        scores.update({
            "score_running_pods": len(running_pods),
            "score_pending_pods": len(pending_pods), # Backlog
        })

        # TODO: Think about this metric as it give you the percentage of the pods that are in the data production phase.
        # scores.update({
        #     "qos_in_data_production": sum(len(running_pods) / sum(len(running_pods) + len(pending_pods))),
        # })

        # Adding scheduler scores
        for k, v in self.scheduler.evaluate(pods, nodes):
            scores[f"score_scheduler_{k}"] = v
        return scores

    def step(self, steps, events=[]):
        # Step: Apply events to the Kubernetes cluster
        # Sub-step: Create new workloads
        for pod in self.create_pods(events, steps):
            self.kube_client.create_object(pod)
            self.logger.info(f'Pod {pod["metadata"]["name"]} is created')

        # Step: Update the simulation model from the cluster
        self.update_pods_on_fake_nodes()
        for node in self.nodes:
            # The node model updates the node state from the Kubernetes cluster
            node.update()

        # Step: Run the scheduler for decisions
        pending_workloads = self.kube_client.v1.list_namespaced_pod("default", field_selector="status.phase=Pending").items
        decisions = self.scheduler.step(pending_workloads, self.nodes)

        # Step: Apply decisions in the cluster
        for pod, node in decisions:
            self.kube_client.placement(pod.metadata.name, node.name)

        # NOTE: Kubernetes metrics server needs some time to update performance metrics
        #       We wait for some time before we can get the updated metrics.
        #       For now we do not use the Kubernetes metrics server,
        #       hence comment out the below line.
        # time.sleep(30)

        # Step: Publish metrics and scores
        metrics = self.aggregate_metrics()
        self.visualization.log_metrics(metrics, step=steps)
        scores = self.calculate_scores()
        self.visualization.log_metrics(scores, step=steps)

    def run(self):
        self.create_cluster()

        # TODO: Simulation runs based on workload creation.
        #       This does not include cases where workloads are finished and
        #       scheduler needs to optimize the current workloads across nodes
        for step in tqdm(range(self.total_steps), desc="Simulation Steps"):
            new_workloads = self.dataloader.next()
            self.step(step, new_workloads)
            time.sleep(1)
