# from ..powermodels.xaviernx import PMXavierNX
import random

class WaggleScheduler():
    def __init__(self):
        self.name = "waggle-scheduler"

    def __str__(self):
        return self.name
    
    def schedule(self, workload, cluster):
        nodes = cluster.nodes
        return workload, nodes[random.randint(0,len(nodes)-1)]

    def step(self, workloads: list, cluster):
        """
        Returns an ordered list of tuples, each tuple containing a workload and a node.
        """
        # TODO: The order should refer to the order in which the workloads are to be scheduled.
        for workload in workloads:
            yield self.schedule(workload, cluster)

    def evaluate(self, cluster):
        return {}