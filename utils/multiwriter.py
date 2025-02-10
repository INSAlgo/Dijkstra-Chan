
import io
import traceback


class MultiWriter(io.StringIO):
    """Writes data to multiple writers.

    This class extends io.StringIO and allows writing data to multiple
    writers simultaneously. It handles exceptions during writing and logs
    errors to a file.
    """

    def __init__(self, *writers, error_file=None):
        self.writers = writers
        self.error_file = error_file or 'error.log'

    def write(self, data):
        for writer in self.writers:
            try:
                writer(data)
            except Exception as e:
                with open(self.error_file, 'a') as file:
                    file.write(f"{str(e)} error while writing to {writer}: {data}")
                    traceback.print_exc(file=file)
