import time

class SimpleCache:
    def __init__(self, ttl=10):
        self.ttl = ttl
        self.data = {}
        self.timestamps = {}

    def get(self, key):
        if key in self.data:
            if time.time() - self.timestamps[key] < self.ttl:
                return self.data[key]
        return None

    def set(self, key, value):
        self.data[key] = value
        self.timestamps[key] = time.time()
