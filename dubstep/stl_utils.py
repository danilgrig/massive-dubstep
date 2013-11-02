from geometry import *
import logging
from interval_tree import IntervalTree
logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.DEBUG, filename=u'sliser.log')


class FormatSTLError(Exception):
    def __init__(self, value=None):
        self.value = value

    def __str__(self):
        return 'FormatSTLError:' + self.value


class StlModel:
    def __init__(self, filename):
        self.filename = filename
        self.facets = []
        self.parse()
        self.direction = '+Z'
        self.ex = dict()
        self.tree = IntervalTree(0)
        self.sorted_z = []
        self.update()

    def __nonzero__(self):
        return True

    def update(self):
        logging.info("Current scales:")
        self.ex = self.get_extremal()
        self.log_scales()
        logging.info('Making tree for STL-model...')
        self.make_tree()
        logging.info('Finished tree.')

    def make_tree(self):
        i = 0
        self.sorted_z = []
        for facet in self.facets:
            self.sorted_z.append((facet.minz(), i))
            self.sorted_z.append((facet.maxz(), i))
            i += 1
        self.sorted_z.sort()

        self.tree = IntervalTree(len(self.sorted_z))
        for facet in self.facets:
            l = self.find_z(facet.minz(), True)
            r = self.find_z(facet.maxz(), False)
            self.tree.push(l, r - 1, facet)

    def intersect_facets(self, z):
        return self.tree.get(self.find_z(z))

    #if bot: returns first element >= z
    #  else: returns first element > z
    def find_z(self, z, bot=False):
        l = 0
        r = len(self.sorted_z)
        while r > l:
            m = (r + l) // 2
            if bot:
                if self.sorted_z[m][0] + EPS > z:
                    r = m
                else:
                    l = m + 1
            else:
                if self.sorted_z[m][0] - EPS > z:
                    r = m
                else:
                    l = m + 1

        # l == r
        return l

    def read_facet(self, f):
        line = f.readline().strip()
        if line != 'outer loop':
            raise ValueError('Expected "outer loop", got "%s"' % line)

        facet = []
        line = f.readline().strip()
        while line != 'endloop':
            parts = line.split()
            if parts[0] != 'vertex':
                raise ValueError('Expected "vertex x y z", got "%s"' % line)
            facet.append(tuple([float(num) for num in parts[1:]]))

            line = f.readline().strip()
        line = f.readline().strip()
        if line != 'endfacet':
            raise ValueError('Expected "endfacet", got "%s"' % line)
        return Facet(Point3(facet[0]), Point3(facet[1]), Point3(facet[2]))

    def log_scales(self):
        e = self.ex
        logging.info('minx = %.3f \t maxx = %.3f' % (e['minx'], e['maxx']))
        logging.info('miny = %.3f \t maxy = %.3f' % (e['miny'], e['maxy']))
        logging.info('minz = %.3f \t maxz = %.3f' % (e['minz'], e['maxz']))

    def parse_text(self):
        f = open(self.filename, 'r')
        logging.info('Parsing STL text model')
        line = f.readline().strip()
        parts = line.split()
        if parts[0] != 'solid':
            raise FormatSTLError('Expected "solid ...", got "%s"' % line)
        name = ' '.join(parts[1:])

        line = f.readline().strip()
        while line.startswith('facet'):
            try:
                facet = self.read_facet(f)
                self.facets.append(facet)
            except AssertionError:
                pass
            line = f.readline().strip()
        if line != ('endsolid %s' % name) and line != "endsolid":
            raise FormatSTLError('Expected "endsolid %s", got "%s"' % (name, line))

    def parse_bin(self):
        file = open(self.filename, 'rb')
        import struct
        try:
            header = file.read(80)
            logging.info('Parsing STL binary model')
            logging.info('HEADER: %s' % header)
            (count,) = struct.unpack('<I', file.read(4))
            logging.info('COUNT: %d' % count)

            for i in range(count):
                normal = struct.unpack('<fff', file.read(12))
                points = []
                for i in range(3):
                    points.append(struct.unpack('<fff', file.read(12)))

                try:
                    f = Facet(Point3(points[0]), Point3(points[1]), Point3(points[2]) )
                    f.normal = Vector3(Point3(normal))
                    f.normal.normalize()
                    self.facets.append(f)
                except AssertionError:
                    pass
                attribute_byte_count = file.read(2)
        except:
            self.facets = []
            raise FormatSTLError

    def parse(self):
        f = open(self.filename, 'r')
        data = f.read()
        if "facet normal" in data[0:300] and "outer loop" in data[0:300]:
            self.parse_text()
        else:
            self.parse_bin()

    def get_extremal(self):
        rand_point = self.facets[0].points[0]
        extremals = {'minx': rand_point.x, 'maxx': rand_point.x,
                     'miny': rand_point.y, 'maxy': rand_point.y,
                     'minz': rand_point.z, 'maxz': rand_point.z}
        for facet in self.facets:
            for p in facet:
                extremals['minx'] = min(extremals['minx'], p.x)
                extremals['maxx'] = max(extremals['maxx'], p.x)

                extremals['miny'] = min(extremals['miny'], p.y)
                extremals['maxy'] = max(extremals['maxy'], p.y)

                extremals['minz'] = min(extremals['minz'], p.z)
                extremals['maxz'] = max(extremals['maxz'], p.z)
        extremals['xsize'] = extremals['maxx'] - extremals['minx']
        extremals['ysize'] = extremals['maxy'] - extremals['miny']
        extremals['zsize'] = extremals['maxz'] - extremals['minz']
        extremals['diameter'] = math.sqrt(extremals['xsize']**2 + extremals['ysize']**2 + extremals['zsize']**2)
        extremals['xcenter'] = (extremals['maxx'] + extremals['minx']) / 2
        extremals['ycenter'] = (extremals['maxy'] + extremals['miny']) / 2
        extremals['zcenter'] = (extremals['maxz'] + extremals['minz']) / 2
        return extremals

    def changeDirection(self, direction):
        #This strange 3 lines make reverse transformation
        for i in range(3):
            for f in self.facets:
                f.changeDirection(self.direction)

        self.direction = direction
        for f in self.facets:
            f.changeDirection(direction)

        self.update()

    def zoom_x(self, scale):
        for f in self.facets:
            f.zoom_x(scale)
        self.update()

    def zoom_y(self, scale):
        for f in self.facets:
            f.zoom_y(scale)
        self.update()

    def zoom_z(self, scale):
        for f in self.facets:
            f.zoom_z(scale)
        self.update()

    def zoom(self, scale):
        for f in self.facets:
            f.zoom(scale)
        self.update()

    def max_size(self):
        max_v = 0
        for v in (self.ex['minx'], self.ex['maxx'], self.ex['miny'], self.ex['maxy'], self.ex['minz'], self.ex['maxz']):
            max_v = max(max_v, abs(v))
        return max_v
