# from ..powermodels.xaviernx import PMXavierNX

class WaggleScheduler():
    def __init__(self):
        self.name = "waggle-scheduler"

    def __str__(self):
        return self.name
    
    def schedule(self, workload, nodes: list):
        return (workload, nodes[0])

    def step(self, workloads: list, nodes: list):
        """
        Returns an ordered list of tuples, each tuple containing a workload and a node.
        """
        # TODO: The order should refer to the order in which the workloads are to be scheduled.
        for workload in workloads:
            yield self.schedule(workload, nodes)

    def evaluate(self, workloads: list, nodes: list):
        return {}