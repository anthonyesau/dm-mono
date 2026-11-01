"""Small geometry toolkit for generating DM Mono glyph outlines.

Contours are stored as a list of on-curve points plus, for every segment
(point i -> point i+1, wrapping), either None (a straight line) or a pair of
bezier handles. Every builder here produces the same point structure no matter
which stroke weight it gets, so the outlines it makes for the Light and Medium
masters stay interpolation-compatible.

Orientation follows Glyphs / PostScript: outer contours counter-clockwise,
counters clockwise. Shapes may overlap; fontmake removes overlaps on export.
"""

import math

KAPPA = 0.5522847498


class Contour:
    def __init__(self, pts, segs=None):
        self.pts = [tuple(map(float, p)) for p in pts]
        self.segs = list(segs) if segs is not None else [None] * len(self.pts)
        assert len(self.segs) == len(self.pts)

    # ------------------------------------------------------------------ basics
    def copy(self):
        return Contour(self.pts, [None if s is None else (tuple(s[0]), tuple(s[1])) for s in self.segs])

    def transform(self, fn):
        """Apply fn(x, y) -> (x, y) to every point (on- and off-curve)."""
        pts = [fn(*p) for p in self.pts]
        segs = [None if s is None else (fn(*s[0]), fn(*s[1])) for s in self.segs]
        return Contour(pts, segs)

    def affine(self, a=1, b=0, c=0, d=1, e=0, f=0):
        c2 = Contour(*_affine_parts(self, a, b, c, d, e, f))
        if a * d - b * c < 0:  # mirroring flips orientation; restore it
            c2 = c2.reversed()
        return c2

    def translate(self, dx, dy):
        return self.affine(1, 0, 0, 1, dx, dy)

    def reversed(self):
        n = len(self.pts)
        pts = [self.pts[0]] + self.pts[:0:-1]
        segs = []
        # new segment k goes from pts[k] to pts[k+1]; in old indexing it is the
        # old segment (n - k - 1) mod n run backwards.
        for k in range(n):
            old = self.segs[(n - k - 1) % n]
            segs.append(None if old is None else (old[1], old[0]))
        return Contour(pts, segs)

    def flatten(self, steps=16):
        out = []
        n = len(self.pts)
        for i in range(n):
            p0, p3 = self.pts[i], self.pts[(i + 1) % n]
            s = self.segs[i]
            if s is None:
                out.append(p0)
            else:
                out += [_bez(p0, s[0], s[1], p3, k / steps) for k in range(steps)]
        return out

    def area(self):
        """Signed area (positive = counter-clockwise)."""
        poly = self.flatten()
        return sum(poly[i - 1][0] * poly[i][1] - poly[i][0] * poly[i - 1][1] for i in range(len(poly))) / 2

    def ccw(self):
        return self if self.area() > 0 else self.reversed()

    def cw(self):
        return self if self.area() < 0 else self.reversed()

    def bounds(self):
        xs, ys = [], []
        n = len(self.pts)
        for i in range(n):
            p0, p3 = self.pts[i], self.pts[(i + 1) % n]
            s = self.segs[i]
            if s is None:
                xs += [p0[0]]; ys += [p0[1]]
            else:
                for t in [j / 16 for j in range(17)]:
                    x, y = _bez(p0, s[0], s[1], p3, t)
                    xs.append(x); ys.append(y)
        return min(xs), min(ys), max(xs), max(ys)

    # ------------------------------------------------------------- Glyphs I/O
    def to_nodes(self, rnd=round):
        """Glyphs-style node list [(x, y, 'line'|'curve'|'offcurve')]."""
        out = []
        n = len(self.pts)
        for i in range(n):
            j = (i + 1) % n
            s = self.segs[i]
            if s is not None:
                out.append((rnd(s[0][0]), rnd(s[0][1]), "offcurve"))
                out.append((rnd(s[1][0]), rnd(s[1][1]), "offcurve"))
                out.append((rnd(self.pts[j][0]), rnd(self.pts[j][1]), "curve"))
            else:
                out.append((rnd(self.pts[j][0]), rnd(self.pts[j][1]), "line"))
        return out

    @classmethod
    def from_nodes(cls, nodes):
        """nodes: [(x, y, type)] in Glyphs closed-path order."""
        start = next(i for i, nd in enumerate(nodes) if nd[2] != "offcurve")
        nodes = nodes[start + 1:] + nodes[:start + 1]  # now ends with an on-curve
        pts, segs, handles = [], [], []
        prev = nodes[-1]
        pts.append((prev[0], prev[1]))
        for nd in nodes:
            if nd[2] == "offcurve":
                handles.append((nd[0], nd[1]))
                continue
            if handles:
                assert len(handles) == 2, "only cubic curves are supported"
                segs.append((handles[0], handles[1]))
            else:
                segs.append(None)
            handles = []
            pts.append((nd[0], nd[1]))
        pts.pop()  # last point duplicates the first
        return cls(pts, segs)


def _affine_parts(c, a, b, cc, d, e, f):
    def fn(x, y):
        return (a * x + cc * y + e, b * x + d * y + f)
    t = c.transform(fn)
    return t.pts, t.segs


def _bez(p0, p1, p2, p3, t):
    mt = 1 - t
    return (
        mt ** 3 * p0[0] + 3 * mt * mt * t * p1[0] + 3 * mt * t * t * p2[0] + t ** 3 * p3[0],
        mt ** 3 * p0[1] + 3 * mt * mt * t * p1[1] + 3 * mt * t * t * p2[1] + t ** 3 * p3[1],
    )


# ---------------------------------------------------------------- primitives

def polygon(points):
    return Contour(points).ccw()


def rect(x0, y0, x1, y1):
    return polygon([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])


def circle(cx, cy, r, ry=None):
    ry = r if ry is None else ry
    k, ky = KAPPA * r, KAPPA * ry
    pts = [(cx, cy - ry), (cx + r, cy), (cx, cy + ry), (cx - r, cy)]
    segs = [
        ((cx + k, cy - ry), (cx + r, cy - ky)),
        ((cx + r, cy + ky), (cx + k, cy + ry)),
        ((cx - k, cy + ry), (cx - r, cy + ky)),
        ((cx - r, cy - ky), (cx - k, cy - ry)),
    ]
    return Contour(pts, segs)


def ring(cx, cy, r, t, ry=None):
    ry = r if ry is None else ry
    return [circle(cx, cy, r, ry), circle(cx, cy, r - t, ry - t).cw()]


def _arc_pts(cx, cy, r, a0, a1, nseg):
    """On-curve points and handle pairs for an arc from a0 to a1 (radians)."""
    step = (a1 - a0) / nseg
    h = 4 / 3 * math.tan(step / 4) * r
    pts, segs = [], []
    for i in range(nseg + 1):
        a = a0 + i * step
        pts.append((cx + r * math.cos(a), cy + r * math.sin(a)))
    for i in range(nseg):
        a, b = a0 + i * step, a0 + (i + 1) * step
        p0, p1 = pts[i], pts[i + 1]
        segs.append(((p0[0] - h * math.sin(a), p0[1] + h * math.cos(a)),
                     (p1[0] + h * math.sin(b), p1[1] - h * math.cos(b))))
    return pts, segs


def arc_stroke(cx, cy, r, t, a0, a1, nseg=None):
    """Stroked open arc (outer radius r) from angle a0 to a1, radial end caps."""
    if nseg is None:
        nseg = max(1, math.ceil(abs(a1 - a0) / (math.pi / 2) - 1e-9))
    op, osg = _arc_pts(cx, cy, r, a0, a1, nseg)
    ip, isg = _arc_pts(cx, cy, r - t, a1, a0, nseg)
    pts = op + ip
    segs = osg + [None] + isg + [None]
    return Contour(pts, segs).ccw()


def line(p0, p1, t):
    """Straight stroke of thickness t with square (perpendicular) ends."""
    (x0, y0), (x1, y1) = p0, p1
    L = math.hypot(x1 - x0, y1 - y0)
    nx, ny = -(y1 - y0) / L * t / 2, (x1 - x0) / L * t / 2
    return polygon([(x0 + nx, y0 + ny), (x0 - nx, y0 - ny), (x1 - nx, y1 - ny), (x1 + nx, y1 + ny)])


def slant_line(p0, p1, t):
    """Stroke between p0 and p1 with horizontal cuts at both ends (like slash)."""
    (x0, y0), (x1, y1) = p0, p1
    ang = math.atan2(abs(y1 - y0), abs(x1 - x0))
    w = t / math.sin(ang) / 2
    return polygon([(x0 - w, y0), (x0 + w, y0), (x1 + w, y1), (x1 - w, y1)])


def hbar(x0, x1, yc, t):
    return rect(x0, yc - t / 2, x1, yc + t / 2)


def vbar(xc, y0, y1, t):
    return rect(xc - t / 2, y0, xc + t / 2, y1)


def _isect(p, d, q, e):
    """Intersection of lines p + s*d and q + u*e."""
    den = d[0] * e[1] - d[1] * e[0]
    s = ((q[0] - p[0]) * e[1] - (q[1] - p[1]) * e[0]) / den
    return (p[0] + s * d[0], p[1] + s * d[1])


def inset_polygon(points, t):
    """Offset a convex CCW polygon inwards by t (mitred corners)."""
    pts = Contour(points).ccw().pts
    n = len(pts)
    lines = []
    for i in range(n):
        a, b = pts[i], pts[(i + 1) % n]
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = math.hypot(dx, dy)
        nx, ny = -dy / L * t, dx / L * t  # left normal = inside for CCW
        lines.append(((a[0] + nx, a[1] + ny), (dx, dy)))
    out = []
    for i in range(n):
        p, d = lines[i - 1]
        q, e = lines[i]
        out.append(_isect(p, d, q, e))
    return out


def polygon_outline(points, t):
    """Outlined (hollow) convex polygon with stroke t drawn inside the path."""
    return [polygon(points), Contour(inset_polygon(points, t)).cw()]


def rotate_pt(p, ang, c=(0, 0)):
    ca, sa = math.cos(ang), math.sin(ang)
    x, y = p[0] - c[0], p[1] - c[1]
    return (c[0] + x * ca - y * sa, c[1] + x * sa + y * ca)


def chevron(tip, direction, arm, t, half_angle=math.radians(45)):
    """Open arrowhead pointing along `direction` with its outer tip at `tip`.

    `arm` is the length of each outer edge; arm ends are cut perpendicular.
    """
    dx, dy = direction
    L = math.hypot(dx, dy)
    d = (dx / L, dy / L)
    back = (-d[0], -d[1])
    a1 = rotate_pt(back, half_angle)
    a2 = rotate_pt(back, -half_angle)
    T = tip
    A1 = (T[0] + a1[0] * arm, T[1] + a1[1] * arm)
    A2 = (T[0] + a2[0] * arm, T[1] + a2[1] * arm)
    # inward normals of each arm point towards the arrow axis
    n1 = rotate_pt(a1, -math.pi / 2)
    n2 = rotate_pt(a2, math.pi / 2)
    B1 = (A1[0] + n1[0] * t, A1[1] + n1[1] * t)
    B2 = (A2[0] + n2[0] * t, A2[1] + n2[1] * t)
    V = (T[0] - d[0] * t / math.sin(half_angle), T[1] - d[1] * t / math.sin(half_angle))
    return polygon([T, A1, B1, V, B2, A2])


def arrowhead(tip, direction, length, half_width):
    """Filled triangular arrowhead with its point at `tip`."""
    d = _unit(direction)
    p = (-d[1], d[0])
    bx, by = tip[0] - d[0] * length, tip[1] - d[1] * length
    return polygon([tip, (bx + p[0] * half_width, by + p[1] * half_width),
                    (bx - p[0] * half_width, by - p[1] * half_width)])


def arrow(tail, tip, t, length, half_width, double=False):
    """Shaft plus filled arrowhead(s), drafting style."""
    dx, dy = tip[0] - tail[0], tip[1] - tail[1]
    L = math.hypot(dx, dy)
    d = (dx / L, dy / L)
    inset = length * 0.6  # shaft ends tucked inside the head
    end = (tip[0] - d[0] * inset, tip[1] - d[1] * inset)
    start = (tail[0] + d[0] * inset, tail[1] + d[1] * inset) if double else tail
    out = [line(start, end, t), arrowhead(tip, d, length, half_width)]
    if double:
        out.append(arrowhead(tail, (-d[0], -d[1]), length, half_width))
    return out


# ----------------------------------------------------- weight-aware scaling

def _unit(v):
    L = math.hypot(*v)
    return (v[0] / L, v[1] / L) if L > 1e-9 else None


def offset(contour, dx, dy, miter_limit=2.5):
    """Grow the ink of a contour by dx horizontally and dy vertically.

    Keeps the point structure unchanged: on-curve points move along the
    (mitred) normal, handles keep their direction and are rescaled by the
    change in chord length of their segment.
    """
    c = contour
    n = len(c.pts)
    moves = []
    for i in range(n):
        p = c.pts[i]
        # incoming tangent
        sin_ = c.segs[i - 1]
        prev_ctrl = sin_[1] if sin_ is not None else c.pts[i - 1]
        tin = _unit((p[0] - prev_ctrl[0], p[1] - prev_ctrl[1]))
        if tin is None and sin_ is not None:
            tin = _unit((p[0] - sin_[0][0], p[1] - sin_[0][1]))
        if tin is None:
            tin = _unit((p[0] - c.pts[i - 1][0], p[1] - c.pts[i - 1][1]))
        sout = c.segs[i]
        next_ctrl = sout[0] if sout is not None else c.pts[(i + 1) % n]
        tout = _unit((next_ctrl[0] - p[0], next_ctrl[1] - p[1]))
        if tout is None and sout is not None:
            tout = _unit((sout[1][0] - p[0], sout[1][1] - p[1]))
        if tout is None:
            nxt = c.pts[(i + 1) % n]
            tout = _unit((nxt[0] - p[0], nxt[1] - p[1]))
        # right-hand normals point away from the ink for CCW outers / CW counters
        n_in = (tin[1], -tin[0])
        n_out = (tout[1], -tout[0])
        dot = n_in[0] * n_out[0] + n_in[1] * n_out[1]
        m = ((n_in[0] + n_out[0]) / (1 + dot), (n_in[1] + n_out[1]) / (1 + dot)) if dot > -0.999 else n_in
        ml = math.hypot(*m)
        if ml > miter_limit:
            m = (m[0] / ml * miter_limit, m[1] / ml * miter_limit)
        moves.append((m[0] * dx, m[1] * dy))
    pts = [(p[0] + mv[0], p[1] + mv[1]) for p, mv in zip(c.pts, moves)]
    segs = []
    for i in range(n):
        s = c.segs[i]
        if s is None:
            segs.append(None)
            continue
        j = (i + 1) % n
        p0, p1 = c.pts[i], c.pts[j]
        q0, q1 = pts[i], pts[j]
        old = math.hypot(p1[0] - p0[0], p1[1] - p0[1])
        new = math.hypot(q1[0] - q0[0], q1[1] - q0[1])
        k = new / old if old > 1e-9 else 1.0
        h0 = (q0[0] + (s[0][0] - p0[0]) * k, q0[1] + (s[0][1] - p0[1]) * k)
        h1 = (q1[0] + (s[1][0] - p1[0]) * k, q1[1] + (s[1][1] - p1[1]) * k)
        segs.append((h0, h1))
    return Contour(pts, segs)


def small_figure(contours, sx, sy, dx, dy, cx_src=300, cx_dst=300, y_dst=0):
    """Scale source contours down and thicken them so stems stay sturdy.

    Source y=0 maps to y_dst + dy (so flat bottoms land on y_dst after
    growing by dy), source x=cx_src maps to cx_dst.
    """
    out = []
    for c in contours:
        s = c.affine(sx, 0, 0, sy, cx_dst - cx_src * sx, y_dst + dy)
        out.append(offset(s, dx, dy))
    return out


# -------------------------------------------------------------------- italic

ITALIC_TAN = math.tan(math.radians(10))
ITALIC_Y0 = 248  # the italic masters are slanted around half the x-height


def slant(contours, tan=ITALIC_TAN, y0=ITALIC_Y0):
    return [c.affine(1, 0, tan, 1, -tan * y0, 0) for c in contours]


def unslant(contours, tan=ITALIC_TAN, y0=ITALIC_Y0):
    return [c.affine(1, 0, -tan, 1, tan * y0, 0) for c in contours]
