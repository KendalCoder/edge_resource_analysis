class Scheduler:
    def __init__(self):
        self.name = ""

    def __str__(self):
        return self.name

    def step(self, workloads: list, cluster):
        raise Exception("the step function must be implemented")
    
    def evaluate(self, cluster):
        return {}