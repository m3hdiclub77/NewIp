import heapq

class TopK:
    def __init__(self, k):
        self.k = k
        self.heap = []

    def push(self, item):
        if len(self.heap) < self.k:
            heapq.heappush(self.heap, item)
        else:
            if item[2] > self.heap[0][2]:
                heapq.heapreplace(self.heap, item)

    def items(self):
        return sorted(self.heap, key=lambda x: x[2], reverse=True)
