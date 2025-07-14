import tensorboardX as tb
from datetime import datetime

class TensorBoard:
    def __init__(self, log_base_dir='logs', scheduler_name='DefaultScheduler'):
        self.log_base_dir = log_base_dir
        self.scheduler_name = scheduler_name
        current_time = datetime.now().strftime('%Y%m%d-%H%M%S')
        log_dir = os.path.join(
            self.log_base_dir, f"{current_time}-{self.scheduler_name}"
        )
        os.makedirs(log_dir, exist_ok=True)
        self.writer = SummaryWriter(log_dir)
        print(f"[TensorBoard] Logging to: {log_dir}")

    def finish(self):
        """Properly close the writer to flush events."""
        self.writer.close()

    def log_metrics(self, metrics: dict, step: int):
        for key, value in metrics.items():
            self.writer.add_scalar(key, value, step)

    def log_scalar(self, tag: str, value: float, step: int):
        self.writer.add_scalar(tag, value, step)

    def log_histogram(self, tag: str, values, step: int):
        self.writer.add_histogram(tag, values, step)

    def log_image(self, tag: str, image, step: int):
        self.writer.add_image(tag, image, step)

    def log_text(self, tag: str, text: str, step: int):
        self.writer.add_text(tag, text, step)

if __name__ == "__main__":
    tb_fairshare = TensorBoard(scheduler_name="FairshareScheduler")
    tb_waggle = TensorBoard(scheduler_name="WaggleScheduler")

    # Example logging
    for step in range(10):
        tb_fairshare.log_scalar("accuracy", 0.8 + 0.01 * step, step)
        tb_waggle.log_scalar("accuracy", 0.85 + 0.01 * step, step)

    tb_fairshare.finish()
    tb_waggle.finish()