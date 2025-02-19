import os

import importlib
import time

from .cluster.kubeclient import KubeClient
from .cluster.test_cluster import TestCluster

from .envconfig import EnvConfig


import yaml
from tqdm import tqdm

class Runner():
    """
        Runner manages the flow of simulation.
    """
    def __init__(self, config: dict, logger):
        self.config = EnvConfig(**config)
        self.logger = logger
        self.total_steps = config.get("steps", 20)
        
        # Choose a cluster
        self.cluster = TestCluster(logger)
        # self.cluster = KubeClient(logger)
        
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

    def cleanup(self):
        self.cluster.cleanup()
        self.visualization.finish()

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
        # for node in self.nodes:
        #     for metric_name, metric_value in node.get_node_metrics():
        #         metrics[f"node_{node}_{metric_name}"] = metric_value
        for node in self.cluster.nodes:
            for metric_name, metric_value in node.get_node_metrics():
                metrics[f"node_{node.name}_{metric_name}"] = metric_value

        metrics.update({
            "cluster_pending_workloads": len(self.cluster.pending_pods),
            "cluster_total_workloads": self.cluster.workloads_total,
        })
        return metrics

    def calculate_scores(self):
        """
        Calculate scores for the simulation.
        """
        scores = {}
        # nodes = self.kube_client.nodes_available()
        # pods = self.kube_client.v1.list_namespaced_pod("default").items

        # # TODO: We need to implement a scoring mechanism for the simulation.
        # #       Scores may include node power consumption, fairness, and other metrics.
        # running_pods = [pod for pod in pods if pod.status.phase == "Running"]
        # pending_pods = [pod for pod in pods if pod.status.phase == "Pending"]

        # scores.update({
        #     "score_running_pods": len(running_pods),
        #     "score_pending_pods": len(pending_pods), # Backlog
        # })

        # TODO: Think about this metric as it give you the percentage of the pods that are in the data production phase.
        # scores.update({
        #     "qos_in_data_production": sum(len(running_pods) / sum(len(running_pods) + len(pending_pods))),
        # })

        # Adding scheduler scores
        for k, v in self.scheduler.evaluate(self.cluster):
            scores[f"score_scheduler_{k}"] = v
        return scores

    def step(self, steps, events=[]):
        # Step: Apply events to the Kubernetes cluster
        # TODO: Create new workloads
        self.cluster.create_new_workloads(events)

        # Step: Update the simulation model from the cluster
        self.cluster.update(step=steps)

        # Step: Run the scheduler for decisions
        pending_workloads = self.cluster.pending_pods
        decisions = self.scheduler.step(pending_workloads, self.cluster)

        # Step: Apply decisions in the cluster
        for pod, node in decisions:
            self.cluster.placement(pod.name, node.name, steps)

        # NOTE: Kubernetes metrics server needs some time to update performance metrics
        #       We wait for some time before we can get the updated metrics.
        #       For now we do not use the Kubernetes metrics server,
        #       hence comment out the below line.
        # time.sleep(30)

        # Step: Publish metrics and scores
        metrics = self.aggregate_metrics()
        self.visualization.log_metrics(metrics, step=steps)
        # scores = self.calculate_scores()
        # self.visualization.log_metrics(scores, step=steps)

    def run(self):
        self.cluster.create_cluster(self.config.hosts)

        # TODO: Simulation runs based on workload creation.
        #       This does not include cases where workloads are finished and
        #       scheduler needs to optimize the current workloads across nodes
        for step in tqdm(range(self.total_steps), desc="Simulation Steps"):
            new_workloads = self.dataloader.next()
            self.step(step, new_workloads)
            time.sleep(1)
