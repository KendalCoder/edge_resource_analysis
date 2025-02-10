# from ..powermodels.xaviernx import PMXavierNX

# Assigns jobs to a random node, irrespective of its load
class FairshareScheduler():
    def __init__(self):
        self.name = "fairshare-scheduler"
        # Quick and dirty way to be able to predict updated node cpu usage (see below)
        self.kube_client = KubeClient(logger)

    def __str__(self):
        return self.name
    
    def schedule(self, tally, workload, nodes: list):
        # calculate intermediate cpu usage by allocating the jobs to fake nodes
        virtual_nodes = nodes.copy()
        for pod, node in tally:
            self.kube_client.placement(pod.metadata.name, node.name)
            node.update()

        # find the least busy node and assign it the job
        memory_usage = [node.metrics["cpu"] for node in virtual_nodes]
        minindex = memory_usage.index(min(memory_usage))
        return (workload, nodes[minindex])

    def step(self, workloads: list, nodes: list):
        tally = []
        for workload in workloads:
            planned_schedule = self.schedule(tally, workload, nodes)
            tally.append(planned_schedule)
            yield planned_schedule
            
