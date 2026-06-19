import time

class RateLimiter:
    def __init__(self, limit):
        self.limit = limit
        self.window = {}
        self.reset_time = 60

    def allow(self, key):
        now = time.time()
        if key not in self.window:
            self.window[key] = []
        self.window[key] = [t for t in self.window[key] if now - t < self.reset_time]
        if len(self.window[key]) < self.limit:
            self.window[key].append(now)
            return True
        return False
