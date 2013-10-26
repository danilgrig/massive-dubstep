import logging

logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.DEBUG, filename=u'sliser.log')


class IntervalTree:
    def __init__(self, size):
        self.size = size
        self.array = []
        for i in range(2 * size + 1):
            self.array.append([])

    def push(self, l, r, element):
        self._push(l + self.size - 1, r + self.size - 1, element)
        return

    def get(self, n):
        return self._get(n + self.size - 1)

    def _push(self, l, r, element):
        if l > r:
            return
        if l == r:
            self.array[l].append(element)
            return

        if l % 2 == 0:
            self.array[l].append(element)
            self._push(l + 1, r, element)
            return

        if r % 2 == 1:
            self.array[r].append(element)
            self._push(l, r - 1, element)
            return

        self._push((l - 1) // 2, (r - 1) // 2, element)
        return

    def _get(self, n):
        ans = []
        while n > 0:
            ans.extend(self.array[n])
            n = (n - 1) // 2

        return ans