class SimpleLoader:
    def __init__(self):
        self.workloads = []
        self.index = 0
        self.load()

    def load(self):
        self.workloads.extend([
            {
                "NAME": "object-counter",
                "REQUEST_CPU": "2000m",
                "REQUEST_MEMORY": "3Gi",
            },
        ])

    def __len__(self):
        return len(self.workloads)

    def __getitem__(self, index):
        return self.workloads[index]
    
    def next(self):
        next_workload = self.workloads[self.index]
        self.index = (self.index+1) % len(self.workloads)
        return [next_workload]