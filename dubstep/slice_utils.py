from time import time
from geometry import *
from loop_utils import Loop
import stl_utils

from interval_tree import IntervalTree
logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.DEBUG, filename=u'sliser.log')

STEP       = 0.5
CORRECTION = 0.001
MAXSIZE    = 200
MAXFACETS  = 30000


class SizeSliceError(Exception):
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return 'FormatSTLError:' + self.value


class Slice:
    def __init__(self, model, z, asrt=True):
        print 'new slice %.2f' % z
        self.asrt = asrt
        self.calculated_fully_scan_old = None
        self.calculated_fully_scan = None
        self.calculated_get_loops = None
        self.calculated_get_shape = None
        self.stl_model = model
        self.z = z
        self.lines = []
        self.ex = {'minx': MAXSIZE, 'maxx': -MAXSIZE,
                   'miny': MAXSIZE, 'maxy': -MAXSIZE}

        if len(model.facets) > MAXFACETS:
            logging.error("Cant slice %d facets. The max supposed numbers of facets is %.2f" %
                          (len(model.facets), MAXFACETS))
            raise SizeSliceError("Cant slice so big model")
        for facet in model.intersect_facets(z):
            if facet.isIntersect(z):
                line = facet.intersect(z)
                if line.length > EPS:
                    self.lines.append(line)

        for line in self.lines:
            for p in line:
                self.ex['minx'] = min(self.ex['minx'], p.x)
                self.ex['maxx'] = max(self.ex['maxx'], p.x)
                self.ex['miny'] = min(self.ex['miny'], p.y)
                self.ex['maxy'] = max(self.ex['maxy'], p.y)

        if self.max_size() > MAXSIZE:
            logging.error("Cant slice %.2f model. The max size is %.2f" % (self.max_size(), MAXSIZE))
            raise SizeSliceError("Cant slice so big model")

        self.sorted_y = []
        self.tree_x = IntervalTree(0)
        print "lines in slice: %d" % len(self.lines)

    def max_size(self):
        x = max(-self.ex['minx'], self.ex['maxx'])
        y = max(-self.ex['miny'], self.ex['maxy'])
        return max(x, y)

    def __len__(self):
        return len(self.lines)

    def __nonzero__(self):
        return True

    #Used it for find first index, self.sorted_y[idx] > y.
    #If there are numbers, equal with y, answer may be any index of them.
    def find_y_old(self, y, asrt=True, left=True):
        l = 0
        r = len(self.sorted_y)
        while r > l:
            m = (r + l) // 2
            if asrt and equal(self.sorted_y[m][0], y):
                logging.info('You want find_y(%.3f) with Assert mode, but there are such y' % y)
                assert 0
            if self.sorted_y[m][0] > y:
                r = m
            else:
                l = m + 1

        # l == r
        return l

    #simple fully scan each STEP row
    #returns list[Line2]
    def fully_scan_old(self):
        if len(self.lines) <= 1:
            return []

        if not self.calculated_fully_scan_old is None:
            return self.calculated_fully_scan_old

        i = 0
        self.sorted_y = []
        for line in self.lines:
            self.sorted_y.append((line.p1.y, i))
            self.sorted_y.append((line.p2.y, -1))
            i += 1
        self.sorted_y.sort()
        self.tree_x = IntervalTree(len(self.sorted_y))
        for line in self.lines:
            l = self.find_y_old(line.p1.y, False)
            r = self.find_y_old(line.p2.y, False)
            if l > r:
                (l, r) = (r, l)
            self.tree_x.push(l, r - 1, line)

        miny = self.ex['miny']
        maxy = self.ex['maxy']

        y = miny + CORRECTION
        ans = []
        number_tries = 0
        while y < maxy:
            while self.exist(y):
                logging.info('Correction in fully_scan_old')
                y += CORRECTION

            if number_tries > 3:
                logging.error("I tired to tries so much! ;(")
                if self.asrt:
                    raise stl_utils.FormatSTLError('Cant slice')
            try:
                ans.extend(self.get_lines_in_row_old(y))
                y += STEP
                number_tries = 0
            except AssertionError:
                y += CORRECTION
                number_tries += 1

        self.calculated_fully_scan = ans
        return ans

    #Remeber, it doesnt work if there is edge in the row
    def get_lines_in_row_old(self, y):
        ans = []
        intersects = []
        index = self.find_y_old(y)

        for line in self.tree_x.get(index):
            if line.isIntersect(y):
                intersects.append(line.calcIntersect(y))
            else:
                logging.info('get_lines_in_row: It can not be! ;(')
                assert 0

        if len(intersects) % 2 == 1:
            logging.error('get_lines_in_row: I have odd number of intersects %f slice %f row. Trying to increment less.' % (self.z, y))
            assert 0
        else:
            intersects.sort()
            for i in range(len(intersects) // 2):
                p1 = Point2(intersects[2 * i], y)
                p2 = Point2(intersects[2 * i + 1], y)
                ans.append(Line2(p1, p2))

        return ans

    #this function is not used now
    def get_points_in_row(self, y):
        intersects = []

        for line in self.lines:
            try:
                if line.isIntersect(y):
                    intersects.append(line.calcIntersect(y))
            except AssertionError:
                intersects.append(line.p1.x)
                intersects.append(line.p2.x)

        intersects.sort()
        ans = [intersects[0]]
        last = ans[0]
        for i in intersects[1:]:
            if abs(i - last) > EPS:
                ans.append(i)
                last = i

        return ans

    #find first element, >= y
    def find_y_left(self, y):
        l = 0
        r = len(self.sorted_y)
        while r > l:
            m = (r + l) // 2
            if self.sorted_y[m][0] + EPS > y:
                r = m
            else:
                l = m + 1

        # l == r
        return l

    #find first element, > y
    def find_y_right(self, y):
        l = 0
        r = len(self.sorted_y)
        while r > l:
            m = (r + l) // 2
            if self.sorted_y[m][0] - EPS > y:
                r = m
            else:
                l = m + 1

        # l == r
        return l

    def find_y(self, y):
        l = 0
        r = len(self.sorted_y)
        while r > l:
            m = (r + l) // 2
            if equal(y, self.sorted_y[m][0]):
                return m
            if self.sorted_y[m][0] > y:
                r = m
            else:
                l = m + 1

        if l == len(self.sorted_y):
            assert 0
        if equal(y, self.sorted_y[l][0]):
            return l

        # not found
        assert 0

    def get_loops(self):
        if not self.calculated_get_loops is None:
            return self.calculated_get_loops

        self.sorted_y = []
        i = 0
        for line in self.lines:
            self.sorted_y.append((line.p1.y, i))
            i += 1
        self.sorted_y.sort()

        ans = []

        checked = []
        for j in range(len(self.lines)):
            checked.append(False)

        for j in range(len(self.lines)):
            if checked[j]:
                continue
            checked[j] = True
            line = self.lines[j]

            loop = [line.p1]
            p = line.p2
            missed = 0
            while p.dist(line.p1) > EPS:
                if p.dist(loop[-1]) > 0.5:
                    loop.append(p)
                else:
                    missed += 1
                nearest = False
                dist = 100
                nearest_idx = -1
                i = self.find_y_left(p.y - CORRECTION)
                while (i < len(self.sorted_y)) and ((self.sorted_y[i][0] - CORRECTION) < p.y):
                    if not checked[self.sorted_y[i][1]]:
                        if p.dist(self.lines[self.sorted_y[i][1]].p1) < dist:
                            dist = p.dist(self.lines[self.sorted_y[i][1]].p1)
                            nearest = self.lines[self.sorted_y[i][1]].p2
                            nearest_idx = self.sorted_y[i][1]

                    i += 1
                if dist > CORRECTION:
                    logging.info("Can't find nearest point. Loop is missed.")
                    loop = []
                    break
                p = nearest
                checked[nearest_idx] = True

            print "point in loop %d" % len(loop)
            print "missed point in loop %d" % missed
            print
            if len(loop) > 2:
                ans.append(Loop(loop))

        self.calculated_get_loops = ans
        return ans

    #fing loops first
    def fully_scan(self):
        if not self.calculated_fully_scan is None:
            return self.calculated_fully_scan
        loops = self.get_loops()

        lines = []
        indx = 0
        for loop in loops:
            prev = loop.points[-1]
            for p in loop:
                lines.append((prev, p, indx, loop.is_hole()))
                prev = p
            indx += 1

        self.sorted_y = []
        for (start, end, i, hole) in lines:
            self.sorted_y.append((start.y, i))
        self.sorted_y.sort()
        self.tree_x = IntervalTree(len(self.sorted_y))

        for (start, end, i, hole) in lines:
            l = self.find_y(start.y)
            r = self.find_y(end.y)
            if l > r:
                (l, r) = (r, l)
            self.tree_x.push(l, r, (start, end, i, hole))

        miny = self.ex['miny']
        maxy = self.ex['maxy']

        y = miny
        ans = []
        while y < maxy:
            while self.exist(y):
                logging.info('Correction in fully_scan')
                y += CORRECTION

            ans.extend(self.get_lines_in_row(y))
            y += STEP

        self.calculated_fully_scan = ans
        return ans

    def exist(self, y):
        try:
            self.find_y(y)
            return True
        except AssertionError:
            return False

    def get_lines_in_row(self, y):
        ans = []
        intersects = []
        index = self.find_y_right(y)

        max_i = 0
        for (start, end, i, hole) in self.tree_x.get(index):
            if i > max_i:
                max_i = i
            line = Line2(start, end)
            if line.isIntersect(y):
                intersects.append((line.calcIntersect(y), i, hole))

        assert len(intersects) % 2 == 0
        active_loop = dict()
        for i in range(max_i + 1):
            active_loop[i] = False

        intersects.sort()
        last = []
        for i in range(len(intersects)):
            if not active_loop[intersects[i][1]]:
                active_loop[intersects[i][1]] = True
                last.append(intersects[i][2])
            else:
                active_loop[intersects[i][1]] = False
                assert last.pop() == intersects[i][2]

            if last and not last[-1]:
                p1 = Point2(intersects[i][0], y)
                p2 = Point2(intersects[i + 1][0], y)
                ans.append(Line2(p1, p2))

        return ans

    def get_shape(self):
        if not self.calculated_get_shape is None:
            return self.calculated_get_shape
        loops = self.get_loops()

        ans = []
        for loop in loops:
            prev = loop.points[-1]
            for p in loop:
                ans.append(Line2(prev, p))
                prev = p

        self.calculated_get_shape = ans
        return ans

if __name__ == '__main__':
#    model = stl_utils.StlModel('C:\\calibration\\pudge.stl')
#    model.zoom(0.1)
    start = time()
    model = stl_utils.StlModel('stl_examples\\pencildome.STL')
    end = time()
    print "load_time = %f" % (end - start)

    start = time()
    model.zoom(1)
    end = time()
    print "zoom_time = %f" % (end - start)

    start = time()
    slice = Slice(model, 10)
    end = time()
    print "prepare_slice_time = %f" % (end - start)

    start = time()
    for loop in slice.get_loops():
#        for p in loop:
#            print p
#        print
#    for loop in slice.fully_scan():
        pass
#        print counter_clock_wise(loop)
#        print p
#        print ' '.join(map(str, list(line)))
    end = time()
    print "making_slice_time = %f" % (end - start)
