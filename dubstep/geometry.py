import math
import logging
logging.basicConfig(format=u'%(levelname)-8s [%(asctime)s] %(message)s',
                    level=logging.DEBUG, filename=u'sliser.log')

EPS = 1e-8


def equal(f1, f2):
    if abs(f1 - f2) < EPS:
        return True
    else:
        return False


def cross3(v1, v2):
    return Vector3(Point3(v1.y * v2.z - v1.z * v2.y,
                         -v1.x * v2.z + v1.z * v2.x,
                          v1.x * v2.y - v1.y * v2.x))


def cross2(v1, v2):
    return v1.x * v2.y - v1.y * v2.x


#you must be careful to provide x1 != x2
def intersect(x1, y1, x2, y2, x):
    y = (y2 - y1) / (x2 - x1) * (x - x1) + y1
    return y


class Point3:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        if type(x) == tuple:
            self.x = x[0]
            self.y = x[1]
            self.z = x[2]
        else:
            self.x = x
            self.y = y
            self.z = z

    def __str__(self):
        s = '(%.6f, %.6f, %.6f) ' % (self.x, self.y, self.z)
        return s

    def __eq__(self, other):
        return equal(self.x, other.x) and equal(self.y, other.y) and equal(self.z, other.z)


class Point2:
    def __init__(self, x=0.0, y=0.0, z=0.0):
        if type(x) == tuple:
            self.x = x[0]
            self.y = x[1]
        else:
            self.x = x
            self.y = y

    def __str__(self):
        s = '(%.6f, %.6f) ' % (self.x, self.y)
        return s

    def __eq__(self, other):
        return equal(self.x, other.x) and equal(self.y, other.y)


class Line3:
    def __init__(self, p1=Point3(), p2=Point3()):
        self.p1 = Point3(p1.x, p1.y, p1.z)
        self.p2 = Point3(p2.x, p2.y, p2.z)

    def __str__(self):
        return str(self.p1) + " -> " + str(self.p2)

    def __eq__(self, other):
        ret = (self.p1 == other.p1 and self.p2 == other.p2) or (self.p1 == other.p2 and self.p2 == other.p1)
        return ret

    def __iter__(self):
        yield self.p1
        yield self.p2

    def length(self):
        dx = self.p1.x - self.p2.x
        dy = self.p1.y - self.p2.y
        dz = self.p1.z - self.p2.z
        sum = dx * dx + dy * dy + dz * dz
        return math.sqrt(sum)

    def isIntersect(self, z):
        if equal(self.p1.z, z) and equal(self.p2.z, z):
            return False
        if (self.p1.z - z) * (self.p2.z - z) <= 0.0:
            return True
        else:
            return False

    def swap(self):
        (self.p1, self.p2) = (self.p2, self.p1)

    def calcIntersect(self, z):
        x1 = self.p1.x
        y1 = self.p1.y
        z1 = self.p1.z

        x2 = self.p2.x
        y2 = self.p2.y
        z2 = self.p2.z

        x = intersect(z1, x1, z2, x2, z)
        y = intersect(z1, y1, z2, y2, z)
        p = Point2(x, y)
        return p


class Line2:
    def __init__(self, p1=Point2(), p2=Point2()):
        self.p1 = Point2(p1.x, p1.y)
        self.p2 = Point2(p2.x, p2.y)

    def __str__(self):
        return str(self.p1) + " -> " + str(self.p2)

    def __eq__(self, other):
        ret = (self.p1 == other.p1 and self.p2 == other.p2) or (self.p1 == other.p2 and self.p2 == other.p1)
        return ret

    def __iter__(self):
        yield self.p1
        yield self.p2

    def length(self):
        dx = self.p1.x - self.p2.x
        dy = self.p1.y - self.p2.y
        sum = dx * dx + dy * dy
        return math.sqrt(sum)

    def failed(self, y):
        if equal(self.p1.y, y) or equal(self.p2.y, y):
            return True
        else:
            return False

    def isIntersect(self, y):
        if equal(self.p1.y, y) and equal(self.p2.y, y):
            assert 0
        if (self.p1.y - y) * (self.p2.y - y) <= 0.0:
            return True
        else:
            return False

    def swap(self):
        (self.p1, self.p2) = (self.p2, self.p1)

    def calcIntersect(self, y):
        x1 = self.p1.x
        y1 = self.p1.y

        x2 = self.p2.x
        y2 = self.p2.y

        x = intersect(y1, x1, y2, x2, y)
        return x


class Vector3:
    def __init__(self, p1=Point3(), p2=Point3()):
        self.x = p1.x - p2.x
        self.y = p1.y - p2.y
        self.z = p1.z - p2.z

    def __str__(self):
        s = 'Vector3(%f, %f, %f) ' % (self.x, self.y, self.z)
        return s


class Facet:
    def __init__(self, p1, p2, p3):
        self.points = (p1, p2, p3, p1)
        v1 = Vector3(p2, p1)
        v2 = Vector3(p3, p1)
        n = cross3(v1, v2)
        self.normal = Vector3(Point3(n.x, n.y, n.z))

    def __str__(self):
        s = 'normal: ' + str(self.normal)
        s += ' points:'
        for p in self.points:
            s += str(p)
        return s

    def __le__(self, z):
        return (self.points[0].z - EPS < z and
                self.points[1].z - EPS < z and
                self.points[2].z - EPS < z)

    def __ge__(self, z):
        return (self.points[0].z + EPS > z and
                self.points[1].z + EPS > z and
                self.points[2].z + EPS > z)

    def __iter__(self):
        yield self.points[0]
        yield self.points[1]
        yield self.points[2]

    def changeDirection(self, direction):
        if direction == '+X':
            for p in self:
                p.x, p.z = p.z, p.x
        elif direction == '-X':
            for p in self:
                p.x, p.z = p.z, -p.x
        elif direction == '+Y':
            for p in self:
                p.y, p.z = p.z, p.y
        elif direction == '-Y':
            for p in self:
                p.y, p.z = p.z, -p.y
        elif direction == '-Z':
            for p in self:
                p.z = -p.z
        elif direction == '+Z':
            pass
        else:
            logging.error('Incorrect direction')

    def zoom(self, scale):
        for p in self:
            p.x *= scale
            p.y *= scale
            p.z *= scale

    def zoom_x(self, scale):
        for p in self:
            p.x *= scale

    def zoom_y(self, scale):
        for p in self:
            p.y *= scale

    def zoom_z(self, scale):
        for p in self:
            p.z *= scale

    def isIntersect(self, z):
        if self >= z or self <= z:
            return False
        else:
            return True

    def intersect(self, z):
        l1 = []
        l2 = []
        for i in range(3):
            p = self.points[i]
            if equal(p.z, z):
                l1.append(i)
            else:
                l2.append(i)

        n = len(l1)
        line = Line3()
        if n == 0:
            l = []
            for j in range(3):
                side = Line3(self.points[j], self.points[j+1])
                if side.isIntersect(z):
                    l.append(side.calcIntersect(z))
            if len(l) != 2:
                logging.error("Error in intersect %d != 2" % len(l))
            line = Line2(l[0], l[1])
        elif n == 1:
            p1 = self.points[l2[0]]
            p2 = self.points[l2[1]]
            p = Line3(p1, p2).calcIntersect(z)
            line = Line2(self.points[l1[0]], p)
        else:
            logging.error("Error in intersect: n > 1")

        v = cross2(self.normal, Vector3(Point3(line.p2.x, line.p2.y), Point3(line.p1.x, line.p1.y)))
        if equal(v, 0.0):
            pass
#            logging.error("v == 0")
        if v < 0.0:
            line.swap()
        return line

