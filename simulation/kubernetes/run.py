import time
import json
import argparse
import logging
import random
import yaml
from string import Template

import wandb

from scheduler.myscheduler import WaggleScheduler

from dataloader.simple import SimpleLoader

from tqdm import tqdm
from kubernetes import client, config, watch, utils


def convert_to_bytes(value):
    """
    Convert a value to bytes.
    """
    if value[-2:] == 'Mi':
        return int(value[:-2]) * 1024 * 1024
    elif value[-2:] == 'Gi':
        return int(value[:-2]) * 1024 * 1024 * 1024
    else:
        return int(value)
    
def convert_to_millicores(value):
    """
    Convert a value to millicores.
    """
    if value[-1] == 'm':
        return int(value[:-1])
    elif value[-1] == 'n':
        return int(value[:-1]) / 1000000
    else:
        return int(value) * 1000


class EnvConfig():
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            if isinstance(value, dict):
                setattr(self, key, EnvConfig(**value))
            elif isinstance(value, list):
                setattr(self, key, [EnvConfig(**v) for v in value])
            else:
                setattr(self, key, value)


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
    
    def placement(self, pod, node, namespace="default"):
        target=client.V1ObjectReference()
        target.kind="Node"
        target.apiVersion="v1"
        target.name= node.metadata.name
        
        meta=client.V1ObjectMeta()
        meta.name=pod.metadata.name
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


class Runner():
    """
        Runner manages the flow of simulation.
    """
    def __init__(self, config: dict, logger):
        self.config = EnvConfig(**config)
        self.kube_client = KubeClient(logger)
        self.logger = logger
        self.total_steps = config.get("steps", 20)

        scheduler_name = self.config.scheduler
        self.logger.info(f'Loading the scheduler {scheduler_name}')
        # TODO: The scheduler module is loaded from the scheduler_name variable
        # self.scheduler = eval(f'{scheduler_name}()')
        self.scheduler = WaggleScheduler()

        dataloader_name = self.config.dataloader
        self.logger.info(f'Loading the dataloader {dataloader_name}')
        # TODO: The dataloader module is loaded from the dataloader_name variable
        # self.dataloader = eval(f'{dataloader_name}()')
        self.dataloader = SimpleLoader()

        visualization_name = self.config.visualization
        self.logger.info(f'Loading the visualization {visualization_name}')
        self.visualization = wandb.init()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.cleanup()

    def create_cluster(self):
        hosts = self.config.hosts
        assert isinstance(hosts, list)
        self.logger.info("Creating nodes...")
        for host in hosts:
            template_path = f'template/{host.type}.yaml.tmpl'
            with open(template_path, "r") as file:
                # node = yaml.safe_load(file.read())
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
            self.logger.info(f'Node {host.name} with the type {host.type} is created')

    def cleanup(self):
        self.kube_client.delete_pods()
        self.visualization.finish()

    def create_pods(self, workloads: dict, steps: int):
        template_path = "template/pod.yaml.tmpl"
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
            with open(template_path, "r") as file:
                t = Template(file.read())
                r = t.substitute({
                    "NAME": pod.metadata.name,
                    "CPU": pod.spec.containers[0].resources.requests["cpu"],
                    "MEMORY": pod.spec.containers[0].resources.requests["memory"],
                })
            resource_usage = yaml.safe_load(r)
            # self.kube_client.create_object(resource_usage)
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

    def aggregate_metrics(self, **entities):
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

        for node in self.kube_client.nodes_available():
            cumulated_cpu = 0
            cumulated_memory = 0
            for pod in self.kube_client.get_pods_on_node(node.metadata.name).items:
                if pod.status.phase != "Running":
                    continue # Skip those pods that are not running

                cumulated_cpu += convert_to_millicores(pod.spec.containers[0].resources.requests["cpu"])
                cumulated_memory += convert_to_bytes(pod.spec.containers[0].resources.requests["memory"])
            metrics.update({
                f'node_{node.metadata.name}_cpu': cumulated_cpu,
                f'node_{node.metadata.name}_memory': cumulated_memory,
            })
        return metrics

    def step(self, steps):
        # Step: Emulate Pods on fake nodes
        self.update_pods_on_fake_nodes()

        # Step: Create new workloads
        new_workloads = self.dataloader.next()
        for pod in self.create_pods(new_workloads, steps):
            self.kube_client.create_object(pod)
            self.logger.info(f'Pod {pod["metadata"]["name"]} is created')

        # Step 2: Run the scheduler for decisions
        pending_workloads = self.kube_client.v1.list_namespaced_pod("default", field_selector="status.phase=Pending").items
        nodes = self.kube_client.nodes_available()
        decisions = self.scheduler.step(pending_workloads, nodes)

        # Step 3: Apply the decisions in the clusters
        for pod_name, node_name in decisions:
            self.kube_client.placement(pod_name, node_name)

        # NOTE: Kubernetes metrics server needs some time to update performance metrics
        #       We wait for some time before we can get the updated metrics.
        #       For now we do not use the Kubernetes metrics server,
        #       hence comment out the below line.
        # time.sleep(30)

        # Step 4: Publish metrics
        metrics = self.aggregate_metrics(decisions=decisions)
        self.visualization.log(metrics, step=steps)

    def run(self):
        self.create_cluster()

        # TODO: Simulation runs based on workload creation.
        #       This does not include cases where workloads are finished and
        #       scheduler needs to optimize the current workloads across nodes
        for step in tqdm(range(self.total_steps), desc="Simulation Steps"):
            self.step(step)
            time.sleep(1)


def main(args):
    with open(args.config, "r") as file:
        config = yaml.safe_load(file)

    with Runner(config=config, logger=logging) as r:
        r.run()
    # w = watch.Watch()
    # for event in w.stream(v1.list_namespaced_pod, "default"):
    #     if event['object'].status.phase == "Pending" and event['object'].spec.scheduler_name == scheduler_name:
    #         try:
    #             res = scheduler(event['object'].metadata.name, random.choice(nodes_available()))
    #             print(res)
    #         except client.rest.ApiException as e:
    #             print(json.loads(e.body)['message'])


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c", "--config", dest="config",
        action="store",
        help="Configuration file in yaml")
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s %(levelname)s - %(filename)s:%(lineno)d: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    exit(main(args))