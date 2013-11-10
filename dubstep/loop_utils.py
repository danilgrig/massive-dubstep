from geometry import *


class Loop:
    def __init__(self, points):
        self.points = points
        self.counter_clock_wise = counter_clock_wise(self.points)

    def __iter__(self):
        return self.points.__iter__()

    def __len__(self):
        return len(self.points)

    def is_hole(self):
        return not self.counter_clock_wise