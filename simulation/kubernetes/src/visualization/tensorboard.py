import tensorflow as tf

class TensorBoard:
    def __init__(self, log_dir='logs'):
        self.log_dir = log_dir
        self.writer = tf.summary.create_file_writer(log_dir)

    def finish(self):
        # No need to close the writer
        pass

    def log_metrics(self, metrics, step):
        with self.writer.as_default():
            for key, value in metrics.items():
                tf.summary.scalar(key, value, step=step)
            self.writer.flush()

    def log_scalar(self, tag, value, step):
        with self.writer.as_default():
            tf.summary.scalar(tag, value, step=step)
            self.writer.flush()

    def log_histogram(self, tag, values, step):
        with self.writer.as_default():
            tf.summary.histogram(tag, values, step=step)
            self.writer.flush()

    def log_image(self, tag, image, step):
        with self.writer.as_default():
            tf.summary.image(tag, image, step=step)
            self.writer.flush()

    def log_text(self, tag, text, step):
        with self.writer.as_default():
            tf.summary.text(tag, text, step=step)
            self.writer.flush()