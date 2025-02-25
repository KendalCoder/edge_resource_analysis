from ..cluster_utils import convert_to_millicores, convert_to_bytes

class SimpleWorkload:
    def __init__(self, pod_template: dict):
        self.name = pod_template["metadata"]["name"]
        self.labels = pod_template["metadata"]["labels"]
        self.state = "Pending"
        self.associated_node_name = ""
        self.started = 0
        # TODO: self.deadline should be based on user requirements
        self.deadline = 5
        self.ended = 0

        self.request_cpu = convert_to_millicores(pod_template["spec"]["containers"][0]["resources"]["requests"]["cpu"])
        self.request_memory = convert_to_bytes(pod_template["spec"]["containers"][0]["resources"]["requests"]["memory"])

    def start_at(self, step):
        self.started = step
        # TODO: We finish the workload in 3 iterations.
        #   We will need to calculate the required steps based on
        #   how much resource the workload gets in each iteration.
        self.ended = step + 3

    def compute(self):
        """
        compute determines whether the workload should be finished.
        """
        pass