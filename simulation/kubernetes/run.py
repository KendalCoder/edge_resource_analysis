import time
import json
import argparse
import logging
import random
import yaml
from string import Template

from scheduler.myscheduler import WaggleScheduler

from dataloader.simple import SimpleLoader

import tqdm
from kubernetes import client, config, watch, utils


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
    def __init__(self):
        config.load_kube_config()
        self.client = client.ApiClient()
        self.v1 = client.CoreV1Api()

    def nodes_available(self):
        ready_nodes = []
        for n in self.v1.list_node().items:
                for status in n.status.conditions:
                    if status.status == "True" and status.type == "Ready":
                        ready_nodes.append(n.metadata.name)
        return ready_nodes
    
    def create_object(self, object_spec, ignore_error=False):
        try:
            return utils.create_from_dict(self.client, object_spec)
        except utils.FailToCreateError as ex:
            if ignore_error:
                return None
            else:
                raise ex
    
    def placement(self, name, node, namespace="default"):
        target=client.V1ObjectReference()
        target.kind="Node"
        target.apiVersion="v1"
        target.name= node
        
        meta=client.V1ObjectMeta()
        meta.name=name
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


class Runner():
    """
        Runner manages the flow of simulation.
    """
    def __init__(self, config: dict, logger):
        self.config = EnvConfig(**config)
        self.kube_client = KubeClient()
        self.logger = logger

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

    def step(self, new_workloads):
        # Step 1: 
        for new_workload in new_workloads:
            pass

        # Step 2: Emulate fake nodes

        # Step 2: Run the scheduler for decisions
        self.scheduler.step()

        # Step 3: Apply the decisions in the clusters

        # Step 4: Publish metrics

    def run(self):
        self.create_cluster()

        # TODO: Simulation runs based on workload creation.
        #       This does not include cases where workloads are finished and
        #       scheduler needs to optimize the current workloads across nodes
        for new_workloads in tqdm(self.dataloader):
            self.step(new_workloads)


def main(args):
    with open(args.config, "r") as file:
        config = yaml.safe_load(file)
    r = Runner(
        config=config,
        logger=logging,
    )
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
        format='%(asctime)s %(levelname)s: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S')

    exit(main(args))