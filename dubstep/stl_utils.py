from geometry import *
import logging
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
        self.ex = self.get_extremal()
        self.logScales()

    def readFacet(self, f):
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

    def logScales(self):
        e = self.ex
        logging.info('minx = %.3f \t maxx = %.3f' % (e['minx'], e['maxx']))
        logging.info('miny = %.3f \t maxy = %.3f' % (e['miny'], e['maxy']))
        logging.info('minz = %.3f \t maxz = %.3f' % (e['minz'], e['maxz']))

    def parseText(self):
        f = open(self.filename, 'r')
        logging.info('Parsing STL text model')
        line = f.readline().strip()
        parts = line.split()
        if parts[0] != 'solid':
            raise FormatSTLError('Expected "solid ...", got "%s"' % line)
        name = ' '.join(parts[1:])

        line = f.readline().strip()
        while line.startswith('facet'):
            self.facets.append(self.readFacet(f))
            line = f.readline().strip()
        if line != ('endsolid %s' % name):
            raise FormatSTLError('Expected "endsolid %s", got "%s"' % (name, line))

    def parseBin(self):
        f = open(self.filename, 'rb')
        import struct
        header = f.read(80)
        logging.info('Parsing STL binary model')
        logging.info('HEADER: %s' % header)
        (count,) = struct.unpack('<I', f.read(4))
        logging.info('COUNT: %d' % count)

        for i in range(count):
            normal = struct.unpack('<fff', f.read(12))
            points = []
            for i in range(3):
                points.append(struct.unpack('<fff', f.read(12)))

            f = Facet(Point3(points[0]), Point3(points[1]), Point3(points[2]) )
            f.normal = Vector3(Point3(normal))
            f.normal.z = 0.0
            self.facets.append(f)
            attribute_byte_count = f.read(2)

    def parse(self):
        f = open(self.filename, 'r')
        data = f.read()
        if "facet normal" in data[1:300] and "outer loop" in data[1:300]:
            self.parseText()
        else:
            self.parseBin()
        return
        #It is not completely true. I have seen *.stl files without "solid" in the begin
        line = self.f.readline().strip()
        self.f.seek(0)
        if line.startswith('solid'):
            return self.parseText()
        else:
            return self.parseBin()

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
        return extremals

    def changeDirection(self, direction):
        #This strange 3 lines make reverse transformation
        for i in range(3):
            for f in self.facets:
                f.changeDirection(self.direction)

        self.direction = direction
        for f in self.facets:
            f.changeDirection(direction)

        logging.info("New scales:")
        self.ex = self.get_extremal()
        self.logScales()

    def zoom_x(self, scale):
        for f in self.facets:
            f.zoom_x(scale)
        logging.info("New scales:")
        self.ex = self.get_extremal()
        self.logScales()

    def zoom_y(self, scale):
        for f in self.facets:
            f.zoom_y(scale)
        logging.info("New scales:")
        self.ex = self.get_extremal()
        self.logScales()

    def zoom_z(self, scale):
        for f in self.facets:
            f.zoom_z(scale)
        logging.info("New scales:")
        self.ex = self.get_extremal()
        self.logScales()

    def zoom(self, scale):
        for f in self.facets:
            f.zoom(scale)
        logging.info("New scales:")
        self.ex = self.get_extremal()
        self.logScales()

    def max_size(self):
        max_v = 0
        for v in self.ex.values():
            max_v = max(max_v, abs(v))
        return max_v
