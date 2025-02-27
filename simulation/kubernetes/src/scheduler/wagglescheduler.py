# from ..powermodels.xaviernx import PMXavierNX
import random

from .scheduler import Scheduler

class WaggleScheduler(Scheduler):
    """
    The current scheduling policy is called "gpu-aware-scheduler" that assigns jobs to nodes based on the GPU availability.
    """
    def __init__(self):
        self.name = "waggle-scheduler"

    def is_node_gpu_available(self, node):
        gpu_pods = [pod for pod in node.pods.values() if pod.labels.get("resource.gpu", False)]
        return node.has_gpu() and len(gpu_pods) == 0
    
    def schedule(self, workload, nodes):
        is_gpu_required = workload.labels.get("resource.gpu", False)
        scores = []
        for node in nodes.values():
            # If the workload does not require GPU we schedule it
            # based on the CPU and memory availability.
            if not is_gpu_required:
                if node.is_workload_fit(workload):
                    scores.append((node.get_resource_score(), node))
            # If the workload requires GPU, we schedule it based on the GPU availability.
            elif self.is_node_gpu_available(node) and node.is_workload_fit(workload):
                scores.append((node.get_resource_score(), node))
        
        # No available node for the workload
        if len(scores) == 0:
            return None
        else:
            scores.sort(key=lambda x: x[0])
            return (workload, scores[0][1])

    def step(self, workloads: list, cluster):
        """
        Returns an ordered list of tuples, each tuple containing a workload and a node.
        """
        # TODO: The order should refer to the order in which the workloads are to be scheduled.
        decisions = []
        virtual_nodes = cluster.nodes.copy()
        for workload in workloads:
            decision = self.schedule(workload, virtual_nodes)
            if decision:
                decisions.append(decision)
                _, virtual_node = decision
                virtual_node.place_pod(workload, cluster.current_step)
        return decisions

    def evaluate(self, cluster):
        return {}