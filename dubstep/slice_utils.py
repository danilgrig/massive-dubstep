from geometry import *
import stl_utils
logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.DEBUG, filename=u'sliser.log')

STEP    = 0.5
EPS     = 0.01
MAXSIZE = 300


class SizeSliceError(Exception):
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return 'FormatSTLError:' + self.value


class Slice:
    def __init__(self, model, z):
        self.z = z
        self.lines = []
        if model.max_size() > MAXSIZE:
            logging.error("Cant slice %.2f model. The max size is %.2f" % (model.max_size(), MAXSIZE))
            raise SizeSliceError("Cant slice so big model")
        for facet in model.facets:
            if facet.isIntersect(z):
                self.lines.append(facet.intersect(z))

    def __len__(self):
        return len(self.lines)

    #simple fully scan each STEP row
    #returns list[Line2]
    def fully_scan(self):
        if len(self.lines) <= 1:
            return []

        miny = self.lines[0].p1.y
        maxy = self.lines[0].p1.y
        for line in self.lines:
            miny = min(miny, line.p1.y)
            maxy = max(maxy, line.p1.y)
            miny = min(miny, line.p2.y)
            maxy = max(maxy, line.p2.y)

        y = miny
        ans = []
        number_tries = 0
        while y < maxy:
            if number_tries > 3:
                logging.error("I tired to tries so much! ;(")
                #raise stl_utils.FormatSTLError('Too much tries have done. Enough!')
                y += STEP
                number_tries = 0
            try:
                ans.extend(self.get_lines_in_row(y))
                y += STEP
                number_tries = 0
            except AssertionError:
                y += EPS
                number_tries += 1

        return ans

    #scans only significant rows
    #returns list[tuple[Point2]]
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

        for line in self.lines:
            if line.failed(y):
                logging.info('get_lines_in_row:  Met vertex on %f slice in %f row. Skipped.' % (self.z, y))
                assert 0

            #not failed yet
            if line.isIntersect(y):
                intersects.append(line.calcIntersect(y))

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

    def make_correct_loops(self):
        print len(self.lines)
        return []
        '''
        lines_dict = dict()

        for line in lines:
            if str(line.p1) not in lines_dict:
                lines_dict[str(line.p1)] = []
            lines_dict[str(line.p1)].append(line.p2)

        ans = []
        for line in lines:
            if len(lines_dict[str(line.p1)]) > 0:
                loop = [line.p1]
                p = lines_dict[str(line.p1)].pop(0)
                while len(lines_dict[str(p)]) > 0:
                    loop.append(p)
                    p = lines_dict[str(p)].pop(0)

                if str(loop[0]) != str(p):
                    logging.error("cant find correct loop!")
                    assert 0

                ans.append(loop)

        return ans
        '''


if __name__ == '__main__':
#    model = stl_utils.StlModel('C:\\calibration\\pudge.stl')
#    model.zoom(0.1)
    model = stl_utils.StlModel('C:\\calibration\\pencildome.stl')
    model.zoom(1)
    slice = Slice(model, 30)
    for line in slice.make_correct_loops():
        print ' '.join(map(str, list(line)))

