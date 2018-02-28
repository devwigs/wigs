# Copyright 2015-2018 D.G. MacCarthy <http://dmaccarthy.github.io>
#
# This file is part of "sc8pr".
#
# "sc8pr" is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# "sc8pr" is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with "sc8pr".  If not, see <http://www.gnu.org/licenses/>.


from random import random
from math import hypot, ceil, sqrt
import pygame
from sc8pr import Graphic, BaseSprite
from sc8pr.util import rgba, hasAny
from sc8pr.geom import transform2dGen, dist, delta, polar2d


class Shape(Graphic):
    _fill = None
    _stroke = rgba((0, 0, 0))
    weight = 1

    @property
    def stroke(self): return self._stroke

    @stroke.setter
    def stroke(self, s): self._stroke = rgba(s) if s else None

    @property
    def fill(self): return self._fill

    @fill.setter
    def fill(self, s): self._fill = rgba(s) if s else None

    @property
    def avgColor(self):
        f = self._fill
        return f if f else self._stroke

    def contains(self, pos):
        "Determine if the point is within the shape, accounting for canvas offset"
        cv = self.canvas
        cvPos = delta(pos, cv.rect.topleft) if cv else pos
        return self.containsPoint(cvPos)


class Circle(Shape):
    radius = None # Override Graphic.radius
#    shape = None
    
    def __init__(self, r):
        self.radius = r
        self._srf = None

    @property
    def size(self):
        d = ceil(2 * self.radius)
        return d, d

    def resize(self, size):
        self.radius = min(size) / 2
        self._srf = None

    def config(self, **kwargs):
        keys = "fill", "stroke", "weight", "radius"
        if hasAny(kwargs, keys): self._srf = None
        return super().config(**kwargs)

    @property
    def image(self):
        if self._srf: return self._srf
        srf = pygame.Surface(self.size, pygame.SRCALPHA)
        r = round(self.radius)
        w = self.weight
        if w: pygame.draw.circle(srf, self._stroke, (r,r), r)
        f = self._fill
        if f or w:
            if not f: f = 0, 0, 0, 0
            pygame.draw.circle(srf, f, (r,r), r-w)
        self._srf = srf
        return srf

    def containsPoint(self, pos):
        "Determine if the point is within the circle; do not account for canvas offset"
        return dist(self.pos, pos) < self.radius

    def intersect(self, other):
        "Find the intersection(s) of two circles as list of points"
        R = self.radius
        r = other.radius
        d = dist(self.pos, other.pos)
        if d > r + R or d == 0 or d < abs(r - R): return []
        r2 = r * r
        x = (d*d + r2 - R*R) / (2*d)
        ux, uy = delta(self.pos, other.pos, 1)
        x0, y0 = other.pos
        x0 += x * ux
        y0 += x * uy
        if x < r:
            y = sqrt(r2 - x*x)
            return [(x0 - y * uy, y0 + y * ux), (x0 + y * uy, y0 - y * ux)]
        else: return [(x0, y0)]


class Line(Shape):
    resolution = 1e-10
    snapshot = None

#     def snapshot(self, **kwargs):
#         msg = "{} does not support snapshot"
#         raise NotImplementedError(msg.format(type(self)))

    def __init__(self, start, point=None, vector=None):
        "Create a line or line segment"
        self.pos = start
        if point:
            ux = point[0] - start[0]
            uy = point[1] - start[1]
        elif type(vector) in (int, float):
            ux = 1
            uy = vector
        else: ux, uy = vector
        self._size = abs(ux), abs(uy)
        u = hypot(ux, uy)
        self.length = u #if point else None
        self.u = ux / u, uy / u

    def __repr__(self):
        if self.length is None: p = " u={}".format(self.u)
        else: p = ",{}".format(self.point(self.length))
        return "<{} {}{}>".format(type(self).__name__, self.pos, p)

    def point(self, s=0):
        "Return the coordinates of a point on the line"
        px, py = self.pos
        ux, uy = self.u
        return px + s * ux, py + s * uy

    def midpoint(self):
        return self.point(self.length/2)

    def parameters(self, pt):
        "Find parameters (s,d) of point q = p0 + s*u + d*n where n is perpendicular to u"
        pos = self.pos
        dx = pt[0] - pos[0]
        dy = pt[1] - pos[1]
        ux, uy = self.u
        return ux * dx + uy * dy, ux * dy - uy * dx
    
    def closest(self, pt):
        "Find the point on the line / segment closest to the specified point"
        s = self.parameters(pt)[0]
        l = self.length
        if l:
            if s < 0: s = 0
            elif s > l: s = l
        return self.point(s)

    def intersect(self, other):
        "Find the intersection of two lines / segments"
        u1x, u1y = self.u
        u2x, u2y = other.u
        det = u2x * u1y - u1x * u2y
        if det:
            p1 = self.pos
            p2 = other.pos
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            s1 = (u2x * dy - u2y * dx) / det
            if self.length is None or (s1 >= 0 and s1 <= self.length):
                s2 = (u1x * dy - u1y * dx) / det
                if other.length is None or (s2 >= 0 and s2 <= other.length):
                    return self.point(s1)
        else: # Lines are parallel
            s0, d = self.parameters(other.point())
            if abs(d) <= self.resolution:
                if self.length is None:  # self is a line
                    return True if other.length is None else other.midpoint()
                if other.length is None: # other is a line
                    return self.midpoint()
                # Both are segments
                s1 = self.parameters(other.point(other.length))[0]
                s0, s1 = min(s0, s1), max(s0, s1)
                s0 = max(0, s0)
                s1 = min(self.length, s1)
                if s1 >= s0: return self.point((s0 + s1) / 2)

# Drawing and canvas interaction

    def draw(self, srf, snapshot=False):
        if self.length is None:
            raise AttributeError("Unable to draw line; segment length not given")
        cv = self.canvas
        dx, dy = (0, 0) if snapshot else cv.rect.topleft
        x1, y1 = self.point(0)
        x2, y2 = self.point(self.length)
        wt = max(1, round(self.weight))
        r = pygame.draw.line(srf, self._stroke, (x1+dx,y1+dy),
            (x2+dx,y2+dy), wt)
        return r.inflate(wt, wt)

    def contains(self, pos):
        return abs(self.parameters(pos)[1]) <= 1 + self.weight / 2

    def resize(self, size):
        ux, uy = self.u
        dx, dy = size
        if ux < 0: dx = -dx
        if uy < 0: dy = -dy
        self.__init__(self.pos, vector=(dx,dy))


class Polygon(Shape):
    _angle = 0

    def setPoints(self, pts, pos=None):
        self.vertices = pts = list(pts)
        self._rect = self._metrics(pts)
        if pos is None: pos = self.center
        elif type(pos) is int: pos = pts[pos]
        self._pos = pos
        self._dumpCache()
        return self

    def __init__(self, pts, pos=None): self.setPoints(pts, pos)

    def _metrics(self, pts):
        (x0, x1), (y0, y1) = tuple((min(x[i] for x in pts),
            max(x[i] for x in pts)) for i in (0,1))
        size = abs(x1 - x0), abs(y1 - y0)
        return (x0, y0), size

    @property
    def center(self):
        corner, size = self._rect
        return tuple(corner[i] + size[i] / 2 for i in (0,1))

    @property
    def size(self): return self._rect[1]

    def blitPosition(self, offset, blitSize):
        "Return the position (top left) to which the graphic is drawn"
        x, y = self._rect[0]
        w = self.weight
        return x + offset[0] - w, y + offset[1] - w

    def config(self, **kwargs):
        keys = "fill", "stroke", "weight"
        if hasAny(kwargs, keys): self._srf = None
        return super().config(**kwargs)

    @property
    def anchor(self): return self._pos

    @anchor.setter
    def anchor(self, pos): self.setPoints(self.vertices, pos)

    @property
    def pos(self): return self._pos

    @pos.setter
    def pos(self, pos):
        xy = self._pos
        dx = pos[0] - xy[0]
        dy = pos[1] - xy[1]
        pts = list((x+dx,y+dy) for (x,y) in self.vertices)
        self.setPoints(pts, pos)

    @property
    def angle(self): return self._angle

    @angle.setter
    def angle(self, a):
        self.transform(a - self._angle)
        self._angle = a

    def transform(self, rotate=0, scale=1):
        "Rotate and scale the Polygon around its anchor point"
        shift = self._pos
        pts = transform2dGen(self.vertices, shift=shift,
            preShift=True, rotate=rotate, scale=scale)
        return self.setPoints(list(pts), self._pos)

    def resize(self, size):
        "Resize the polygon (e.g. when scaling the canvas)"
        w, h = self._rect[1]
        f = size[0] / w, size[1] / h
        print(w, h, size, f)
        self.transform(scale=f)
        return f

    def _dumpCache(self):
        self._srf = None
        self._segCache = None

    @property
    def image(self):
        "Return the most recent rendered Surface"
        if self._srf is None: self._srf = self._render()
        return self._srf

    def _render(self):
        "Render the polygon onto a new Surface"
        w, f, s = round(self.weight), self._fill, self._stroke
        dx, dy = self._rect[0]
        dx = w - dx
        dy = w - dy
        size = self.size
        size = 2 * w + size[0], 2 * w + size[1] 
        srf = pygame.Surface(size, pygame.SRCALPHA)
#        pts = list((x+dx,y+dy) for (x,y) in self.vertices)
        pts = [(round(x+dx), round(y+dy)) for (x,y) in self.vertices]
        if f: pygame.draw.polygon(srf, f, pts)
        if w and s: pygame.draw.polygon(srf, s, pts, w)
        return srf

    def _segments(self):
        "Generate the line segments of the polygon"
        pts = self.vertices
        p1 = pts[-1]
        for i in range(len(pts)):
            p2 = pts[i]
            yield Line(p1, p2)
            p1 = p2

    @ property
    def segments(self):
        if not self._segCache: self._segCache = list(self._segments())
        return self._segCache

    def intersect(self, other):
        "Find intersection(s) of polygon with another polygon or line as list of points"
        pts = []
        if isinstance(other, Polygon): other = other.segments
        else: other = other,
        for s in self.segments:
            for so in other:
                pt = s.intersect(so)
                if pt: pts.append(pt)
        return pts

    def containsPoint(self, pos):
        "Determine if the point is within the polygon; do not account for canvas offset"
        x, y = self._rect[0]
        l = Line(pos, (x - 2 * self.weight, y - random()))
        n = 0
        for s in self._segments():
            if s.intersect(l): n += 1
        return n % 2 == 1


class Arrow(Polygon):
    "Arrow shaped graphic"

    def __init__(self, length, width=0.1, head=0.1, flatness=2):
        width *= length / 2
        head *= length
        y = head * flatness / 2
        pts = [(0,0), (-head, y), (-head, width), (-length, width),
            (-length, -width), (-head, -width), (-head, -y)]
        super().__init__(pts, 0)

    @staticmethod
    def between(tail, tip, width=0.1, head=0.1, flatness=2):
        r, a = polar2d(*delta(tip, tail))
        return Arrow(r, width, head, flatness).config(pos=tip, angle=a)


class CircleSprite(Circle, BaseSprite): pass
class PolygonSprite(Polygon, BaseSprite): pass
class ArrowSprite(Arrow, BaseSprite): pass
