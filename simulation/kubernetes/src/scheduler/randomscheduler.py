# from ..powermodels.xaviernx import PMXavierNX
import random

# Assigns jobs to a random node, irrespective of its load
class RandomScheduler():
    def __init__(self):
        self.name = "random-scheduler"

    def __str__(self):
        return self.name
    
    def schedule(self, workload, nodes: list):
        return (workload, nodes[random.randint(0,len(nodes)-1)])
    
    def step(self, workloads: list, nodes: list):
        for workload in workloads:
            yield self.schedule(workload, nodes)

    def evaluate(self, workloads: list, nodes: list):
        return {}
