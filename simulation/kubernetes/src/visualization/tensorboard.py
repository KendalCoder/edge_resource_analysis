import tensorboardX as tb
from datetime import datetime

class TensorBoard:
    def __init__(self, log_dir='logs'):
        self.log_dir = log_dir
        current_time = datetime.now().strftime('%Y%m%d-%H%M%S')
        log_dir_with_timestamp = f"{self.log_dir}/{current_time}"
        self.writer = tb.SummaryWriter(log_dir_with_timestamp)

    def finish(self):
        # No need to close the writer
        pass

    def log_metrics(self, metrics, step):
        for key, value in metrics.items():
            self.writer.add_scalar(key, value, step)

    def log_scalar(self, tag, value, step):
        self.writer.add_scalar(tag, value, step)

    def log_histogram(self, tag, values, step):
        self.writer.add_histogram(tag, values, step)

    def log_image(self, tag, image, step):
        self.writer.add_image(tag, image, step)

    def log_text(self, tag, text, step):
        self.writer.add_text(tag, text, step)
