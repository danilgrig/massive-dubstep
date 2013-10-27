from time import time
from geometry import *
import stl_utils
from interval_tree import IntervalTree
logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.DEBUG, filename=u'sliser.log')

STEP       = 0.2
CORRECTION = 0.001
#EPS        = 0.001
MAXSIZE    = 350
MAXFACETS  = 10000


class SizeSliceError(Exception):
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return 'FormatSTLError:' + self.value


class Slice:
    def __init__(self, model, z):
        self.stl_model = model
        self.z = z
        self.lines = []
        self.sorted_y = []
        self.ex = {'minx': MAXSIZE, 'maxx': -MAXSIZE,
                   'miny': MAXSIZE, 'maxy': -MAXSIZE}
        if self.stl_model.loaded:
            if model.max_size() > MAXSIZE:
                logging.error("Cant slice %.2f model. The max size is %.2f" % (model.max_size(), MAXSIZE))
                raise SizeSliceError("Cant slice so big model")
            if len(model.facets) > MAXFACETS:
                logging.error("Cant slice %d facets. The max supposed numbers of facets is %.2f" %
                              (len(model.facets), MAXFACETS))
                raise SizeSliceError("Cant slice so big model")
            for facet in model.facets:
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

            i = 0
            for line in self.lines:
                self.sorted_y.append((line.p1.y, i))
                self.sorted_y.append((line.p2.y, -1))
                i += 1
            self.sorted_y.sort()

            #making interval tree for fast search intersected lines
            self.tree_x = IntervalTree(0)
        else:
            assert 0

    def setHeight(self, height):
        # Set new height and recalculate list of facets
        self.z = height
        self.lines = []
        if self.stl_model and self.stl_model.max_size() > MAXSIZE:
            logging.error("Cant slice %.2f model. The max size is %.2f" % (model.max_size(), MAXSIZE))
            raise SizeSliceError("Cant slice so big model")
        for facet in self.stl_model.facets:
            if facet.isIntersect(self.z):
                self.lines.append(facet.intersect(self.z))


    def __len__(self):
        return len(self.lines)

    #Used it for find first index, self.sorted_y[idx] > y.
    #If there are numbers, equal with y, answer may be any index of them.
    def find_y(self, y, asrt=True):
        l = 0
        r = len(self.sorted_y)
        while r > l:
            m = (r + l) // 2
            if asrt:
                if equal(self.sorted_y[m][0], y):
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
    def fully_scan(self):
        if len(self.lines) <= 1:
            return []

        self.tree_x = IntervalTree(len(self.sorted_y))
        for line in self.lines:
            l = self.find_y(line.p1.y, False)
            r = self.find_y(line.p2.y, False)
            if l > r:
                (l, r) = (r, l)
            self.tree_x.push(l, r - 1, line)

        miny = self.ex['miny']
        maxy = self.ex['maxy']

        y = miny + CORRECTION
        ans = []
        number_tries = 0
        while y < maxy:
            if number_tries > 3:
                logging.error("I tired to tries so much! ;(")
                raise stl_utils.FormatSTLError('Cant slice')
            try:
                ans.extend(self.get_lines_in_row(y))
                y += STEP
                number_tries = 0
            except AssertionError:
                y += CORRECTION
                number_tries += 1

        return ans

    #scans only significant rows
    #returns list[tuple[Point2]]
    #it wasn't a good idea. no profit
    def intellectual_scan(self):
        if len(self.lines) <= 1:
            return []

        all_y = []
        for line in self.lines:
            all_y.append(line.p1.y)
            all_y.append(line.p2.y)
        all_y.sort()

        ans = []
        y_prev = all_y[0]
        for y_next in all_y[1:]:
            if y_next - STEP / 5 < y_prev:
                y_prev = y_next
                continue
            try:
                lines_prev = self.get_lines_in_row(y_prev + EPS)
                lines_next = self.get_lines_in_row(y_next - EPS)
            except:
                logging.error("Can't get_lines_in_row. %f slice, %f row" % (self.z, y_next))
                raise stl_utils.FormatSTLError("Can't get_lines_in_row. %f slice, %f row" % (self.z, y_next))
                #continue

            if len(lines_prev) != len(lines_next):
                logging.error("Ooops, the lengths is not equal!")
                raise stl_utils.FormatSTLError("Ooops, the lengths is not equal! Row %f" % y_next)
                #continue

            for i in range(len(lines_prev)):
                ans.append((lines_prev[i].p1, lines_prev[i].p2, lines_next[i].p2, lines_next[i].p1))
            y_prev = y_next

        return ans

    #Remeber, it doesnt work if there is edge in the row
    def get_lines_in_row(self, y):
        ans = []
        intersects = []
        index = self.find_y(y)

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

    def get_loops(self):
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
            while p.dist(line.p1) > EPS:
                loop.append(p)
                nearest = False
                dist = 100
                nearest_idx = -1
                i = self.find_y(p.y - CORRECTION)
                while (i < len(self.sorted_y)) and ((self.sorted_y[i][0] - CORRECTION) < p.y):
                    if self.sorted_y[i][1] != -1 and not checked[self.sorted_y[i][1]]:
                        if p.dist(self.lines[self.sorted_y[i][1]].p1) < dist:
                            dist = p.dist(self.lines[self.sorted_y[i][1]].p1)
                            nearest = self.lines[self.sorted_y[i][1]].p2
                            nearest_idx = self.sorted_y[i][1]

                    i += 1
                if dist > CORRECTION:
                    logging.error("Can't find nearest point. Loop is missed.")
                    loop = []
                    break
                p = nearest
                checked[nearest_idx] = True
            if len(loop) > 2:
                ans.append(loop)
        return ans


if __name__ == '__main__':
#    model = stl_utils.StlModel('C:\\calibration\\pudge.stl')
#    model.zoom(0.1)
    model = stl_utils.StlModel('stl_examples\\pudge.stl')
    model.zoom(0.08)
    slice = Slice(model, 10)
    start = time()
    for loop in slice.get_loops():
        print counter_clock_wise(loop)
#        print p
#        print ' '.join(map(str, list(line)))
    end = time()
    print "time = %f" % (end - start)
