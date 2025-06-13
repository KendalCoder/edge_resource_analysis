from .scheduler import Scheduler

class WorkloadAwareScheduler(Scheduler):
    """
    WorkloadAwareScheduler takes into account hard constraints of workloads.
    For example, when some workloads require GPU to run it tries to avoid placing
    non-GPU workloads on the same node if they do not finish before the GPU workload comes in.
    """
    def __init__(self):
        self.name = "workload-aware-scheduler"

    def is_node_gpu_available(self, node):
        gpu_pods = [pod for pod in node.pods.values() if pod.labels.get("resource.gpu", False)]
        return node.has_gpu() and len(gpu_pods) == 0
    
    def schedule(self, workload, nodes):
        # TODO: Consider the current loads on the nodes and avoid placing workloads without constraints
        #  on the special nodes that might need to be reserved for the workloads with constraints.
        pass

    def step(self, workloads: list, cluster):
        """
        Returns an ordered list of tuples, each tuple containing a workload and a node.
        """
        decisions = []
        return decisions

    def evaluate(self, cluster):
        return {}