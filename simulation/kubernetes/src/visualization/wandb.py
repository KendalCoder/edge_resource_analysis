import wandb

class WanDB:
    def __init__(self, project_name, entity=None):
        self.project_name = project_name
        self.entity = entity
        self.run = None
        self.start()

    def start(self, run_name=None):
        self.run = wandb.init(project=self.project_name, entity=self.entity, name=run_name)

    def log_metrics(self, metrics, steps=None):
        if steps is None:
            wandb.log(metrics)
        else:
            wandb.log(metrics, step=steps)

    def finish(self):
        if self.run is not None:
            self.run.finish()
        else:
            raise RuntimeError("Run has not been started. Call start_run() before finishing run.")