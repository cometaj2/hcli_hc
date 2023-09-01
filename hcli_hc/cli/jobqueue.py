import queue as q


# Singleton Job Queue for sequential streaming jobs in a single process multithread environment
class JobQueue:
    instance = None
    queue = None

    def __new__(self):
        if self.instance is None:

            self.instance = super().__new__(self)
            self.queue = q.Queue()

        return self.instance

    # adds a named job to the queue
    def put(self, function):
        return self.queue.put(function)

    def get(self):
        return self.queue.get(self)

    def qsize(self):
        return self.queue.qsize()

    def empty(self):
        return self.queue.empty()

    def clear(self):
        return self.queue.queue.clear()
