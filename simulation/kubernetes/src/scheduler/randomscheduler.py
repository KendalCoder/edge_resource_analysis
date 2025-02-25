# from ..powermodels.xaviernx import PMXavierNX
import random

# Assigns jobs to a random node, irrespective of its load
class RandomScheduler():
    def __init__(self):
        self.name = "random-scheduler"

    def schedule(self, workload, cluster):
        nodes = cluster.nodes
        return workload, nodes[random.randint(0,len(nodes)-1)]

    def step(self, workloads: list, cluster):
        """
        Returns an ordered list of tuples, each tuple containing a workload and a node.
        """
        # TODO: The order should refer to the order in which the workloads are to be scheduled.
        decisions = [self.schedule(workload, cluster) for workload in workloads]
        return decisions

    def evaluate(self, workloads: list, nodes: list):
        return {}
