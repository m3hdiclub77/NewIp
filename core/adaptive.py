class AdaptiveWorkers:
    def __init__(self, min_w, max_w, queue):
        self.min_w = min_w
        self.max_w = max_w
        self.queue = queue

    def compute(self):
        q = self.queue.qsize()

        if q > self.queue.maxsize * 0.8:
            return self.max_w
        if q < self.queue.maxsize * 0.3:
            return self.min_w

        return (self.min_w + self.max_w) // 2
