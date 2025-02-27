from .scheduler import Scheduler

# Assigns jobs to a random node, irrespective of its load
class FairshareScheduler(Scheduler):
    def __init__(self):
        self.name = "fairshare-scheduler"
    
    def schedule(self, tally, workload, nodes: list):
        # find the least busy node and assign it the job
        cpu_usage = [node.metrics["cpu"] for node in nodes]
        minindex = cpu_usage.index(min(cpu_usage))
        if nodes[minindex].is_workload_fit(workload):
            return (workload, nodes[minindex])
        else:
            return None

    def step(self, workloads: list, cluster):
        tally = []
        virtual_nodes = cluster.nodes.copy()
        for workload in workloads:
            planned_schedule = self.schedule(tally, workload, list(virtual_nodes.values()))
            # If the workload cannot be scheduled, skip it
            if planned_schedule is None:
                continue

            # Update the virtual node with the new job placement
            _, virtual_node = planned_schedule
            virtual_node.place_pod(workload, cluster.current_step)

            tally.append(planned_schedule)
        return tally