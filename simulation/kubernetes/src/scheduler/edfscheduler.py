# from ..powermodels.xaviernx import PMXavierNX
import random
# Assigns jobs to a random node, irrespective of its load
class EDFScheduler():
    def __init__(self):
        self.name = "edf-scheduler"

    def __str__(self):
        return self.name
    
    def schedule(self, workload, nodes: list):
        validjob = false
        for node in nodes:
            validjob = validjob or check_constraints(workload,node)
            if validjob:
                return (workload, node)

    # TODO: Rename runtime to deadline
    # TODO: Pass the resources including cpu and memory to the nodes object
    #  so that the scheduler can check the constraints before assigning the job to the node.
    def step(self, workloads: list, nodes: list):
        sorted_workloads = sorted(workloads, key=lambda job: job.runtime)
        for workload in sorted_workloads:
            yield self.schedule(workload, nodes)

    def evaluate(self, workloads: list, nodes: list):
        return {}

  # Checks constraints on the CPU, returning FALSE if
  # adding the job would violate any constraints, TRUE otherwise.
    def check_constraints(workload, node)
        return (workload.request_cpu < convert_to_millicores(node.status.capacity["cpu"]) - node.metrics["cpu"])
