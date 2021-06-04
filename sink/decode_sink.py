from multiprocessing import Process, Event


class DecodeSink(Process):
    """
    信号解析基本类
    """
    def __init__(self, decode_queue, queue):
        super().__init__()
        self.decode_queue = decode_queue
        self.msg_queue = queue
        self.exit = Event()

    def run(self):
        pass
