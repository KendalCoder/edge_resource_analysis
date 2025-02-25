from .scheduler import Scheduler

class EDFScheduler(Scheduler):
    def __init__(self):
        self.name = "edf-scheduler"
    
    def schedule(self, workload, nodes: list):
        # TODO: Checks constraints on the CPU, returning FALSE if
        #   adding the job would violate any constraints, TRUE otherwise.
        for node in nodes:
            if node.is_workload_fit(workload):
                return (workload, node)
        return None

    def step(self, workloads: list, cluster):
        decisions = []
        # Ascending sort by deadline
        sorted_workloads = sorted(workloads, key=lambda job: job.deadline)
        for workload in sorted_workloads:
            decision = self.schedule(workload, cluster.nodes)
            if decision is None:
                continue
            decisions.append(decision)
        return decisions
