"""Corne LP (corne-chocolate v3 / Helidox) wrap case, parametric model.

Two printed parts per half:
  shell  deck (= switch plate) + walls + controller hump, wraps to the bottom
  floor  drops in from below; M2 screws go up through floor + PCB into blind bosses

Coords: X,Y = KiCad PCB coords with Y flipped; Z = 0 at PCB top. The left half is
the PCB as drawn, the right half is its mirror. pcb.json holds Edge.Cuts and
footprint positions from foostan/crkbd@v3-final corne-chocolate.kicad_pcb.

Mesh CSG (manifold3d) with lofted skins; outputs STL.
Build:  uv run --python 3.12 --with manifold3d --with shapely --with numpy case.py
"""
import json
import math
from pathlib import Path

import numpy as np
from manifold3d import CrossSection, Manifold, Mesh, OpType, set_circular_segments, triangulate
from shapely.geometry import LineString, Point, Polygon, box
from shapely.geometry.polygon import orient
from shapely.ops import polygonize, unary_union

set_circular_segments(64)
HERE = Path(__file__).parent
P = dict(
    clr=0.5,            # PCB edge -> inner wall
    wall=2.2,
    corner_r=5.0,       # plan-view rounding
    top_r=2.0,          # deck edge round-over
    tuck_h=6.0,         # soft under-curve: height ...
    tuck_in=3.0,        # ... and how far it pulls in at the bottom
    plate_z=2.2,        # deck bottom = choc plate height above PCB
    deck_t=1.3,         # deck = integrated switch plate
    key_hole=14.0,
    socket_clear=2.0,   # hotswap sockets are 1.85
    battery=(34.0, 49.0, 6.0),  # EEMB 603449 (w, l, t)
    battery_at=(118.0, 100.0),  # centre (KiCad coords), long side along X
    battery_gap=0.3,
    floor_t=1.2,
    floor_tol=0.2,
    # controller column: nice!nano on stock headers + black spacer
    nano=(185.75, 86.25), nano_z=2.5,  # board underside above PCB
    hump_x=(174.0, 194.75), hump_y=(60.0, 118.0),
    hump_top=12.0, hump_wall=1.6, hump_r=5.0, hump_top_r=2.5,
    oled_win=(185.1, 84.0, 8.0, 25.0),  # cx, cy, w, h
    reset=(192.9, 107.0), reset_hole=3.2,
    usb=(185.75, 5.1, 12.5, 7.5),       # cx, cz, w, h
    pim=(185.9, 88.0, 22.4, 25.4),      # cx, cy, w, h (PIM447 is 25 x 22 x 9.5)
    pim_ledge_z=7.0,
    screws=[(79.5, 86.75), (79.5, 105.5), (122.75, 122.75), (169.25, 130.5), (155.5, 83.0)],
    boss_d=4.4, pilot_d=1.7, clear_d=2.3, head_d=4.2, head_h=1.6, standoff_d=5.6,
    magsafe=(141.0, 96.0, 56.5, 45.5, 0.6),  # cx, cy, OD, ID, depth
)

Z_DECK = P["plate_z"] + P["deck_t"]
Z_PCB_BOT = -1.6
Z_SOCK = Z_PCB_BOT - P["socket_clear"]
Z_FLOOR = Z_SOCK - P["battery"][2] - P["battery_gap"]
Z_BOT = Z_FLOOR - P["floor_t"]


# ---- PCB data ----------------------------------------------------------------
def _arc(a, m, b, n=24):
    (x1, y1), (x2, y2), (x3, y3) = a, m, b
    d = 2 * (x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
    ux = ((x1**2 + y1**2) * (y2 - y3) + (x2**2 + y2**2) * (y3 - y1) + (x3**2 + y3**2) * (y1 - y2)) / d
    uy = ((x1**2 + y1**2) * (x3 - x2) + (x2**2 + y2**2) * (x1 - x3) + (x3**2 + y3**2) * (x2 - x1)) / d
    r = math.hypot(x1 - ux, y1 - uy)
    t1, t2, t3 = (math.atan2(p[1] - uy, p[0] - ux) for p in (a, m, b))
    ccw = lambda f, t: (t - f) % (2 * math.pi)
    sweep = ccw(t1, t3)
    if ccw(t1, t2) > sweep:
        sweep -= 2 * math.pi
    pts = [(ux + r * math.cos(t1 + sweep * i / n), uy + r * math.sin(t1 + sweep * i / n)) for i in range(n + 1)]
    pts[0], pts[-1] = a, b
    return pts


def pcb_data():
    return json.loads((HERE / "pcb.json").read_text())


def pcb_outline() -> Polygon:
    seen, lines = [], []

    def snap(p):  # the KiCad outline has a 2 um gap
        for q in seen:
            if abs(p[0] - q[0]) < 0.01 and abs(p[1] - q[1]) < 0.01:
                return q
        seen.append(p)
        return p

    for s in pcb_data()["segs"]:
        a, b = snap((s["start"][0], -s["start"][1])), snap((s["end"][0], -s["end"][1]))
        pts = [a, b] if s["kind"] == "line" else _arc(a, (s["mid"][0], -s["mid"][1]), b)
        lines.append(LineString(pts))
    biggest = max(polygonize(unary_union(lines)), key=lambda p: p.area)
    return Polygon(biggest.exterior)  # drop the LED windows


def keys():
    return [(x, -y, r) for n, x, y, r in pcb_data()["fps"] if "Choc" in n]


def xy(x, ky):
    return (x, -ky)


# ---- 2D (shapely) -------------------------------------------------------------
def off(poly, d):
    return poly.buffer(d, join_style="round", quad_segs=16)


def round2d(poly, r):
    return off(off(off(off(poly, r), -r), -r), r)


def rect(cx, cy, w, h, r=0.0):
    b = box(cx - w / 2, cy - h / 2, cx + w / 2, cy + h / 2)
    return round2d(b, r) if r else b


def cs(poly) -> CrossSection:
    loops = []
    for p in (q for q in getattr(poly, "geoms", [poly]) if q.area > 0.01):
        p = orient(p, 1.0)
        loops.append(np.array(p.exterior.coords[:-1]))
        loops += [np.array(h.coords[:-1]) for h in p.interiors]
    return CrossSection(loops)


# ---- 3D -------------------------------------------------------------------------
def slab(poly, z0, z1):
    return Manifold.extrude(cs(poly), z1 - z0).translate((0, 0, z0))


def union(parts):
    return Manifold.batch_boolean(parts, OpType.Add)


def cyl(x, y, z0, z1, d):
    return Manifold.cylinder(z1 - z0, d / 2).translate((x, y, z0))


def cube(cx, cy, cz, w, d, h, rot=0.0):
    return Manifold.cube((w, d, h), center=True).rotate((0, 0, rot)).translate((cx, cy, cz))


def loft(base, profile, n=900):
    """Smooth solid through (z, inset) sections of `base`. Each section's points are
    projections of the base ring's points, so the side quads don't twist.
    Insets must stay below the base's smallest convex corner radius."""
    br = orient(base, 1.0).exterior
    start = br.project(Point(br.centroid.x, br.centroid.y + 1000))
    pts = [br.interpolate((start + br.length * i / n) % br.length) for i in range(n)]
    rings = []
    for z, ins in profile:
        r = orient(off(base, -ins), 1.0).exterior if ins > 1e-6 else br
        rings.append([(q.x, q.y, z) for q in (r.interpolate(r.project(p)) for p in pts)])
    verts = np.array([v for rg in rings for v in rg], dtype=np.float32)
    tris = []
    for k in range(len(rings) - 1):
        a, b = k * n, (k + 1) * n
        for i in range(n):
            j = (i + 1) % n
            tris += [(a + i, a + j, b + j), (a + i, b + j, b + i)]
    for k, flip in ((0, True), (len(rings) - 1, False)):
        for t in triangulate([np.array([v[:2] for v in rings[k]])]):
            t = [int(i) + k * n for i in t]
            tris.append((t[0], t[2], t[1]) if flip else tuple(t))
    m = Manifold(Mesh(vert_properties=verts, tri_verts=np.array(tris, dtype=np.uint32)))
    assert m.status().name == "NoError", m.status()
    return m


def round_over(z0, z1, inset, n):
    """quarter circle: straight at z0, fully inset at z1"""
    return [(z0 + (z1 - z0) * math.sin(a), inset * (1 - math.cos(a)))
            for a in (k / n * math.pi / 2 for k in range(n + 1))]


def tuck(z0, z1, inset, n):
    """quarter ellipse: fully inset at z0, straight at z1"""
    return sorted((z1 - (z1 - z0) * math.sin(a), inset * (1 - math.cos(a)))
                  for a in (k / n * math.pi / 2 for k in range(n + 1)))


def tuck_inset(z):
    v = min(max((Z_BOT + P["tuck_h"] - z) / P["tuck_h"], 0), 1)
    return P["tuck_in"] * (1 - math.sqrt(1 - v * v))


# ---- parts ------------------------------------------------------------------
def outlines():
    pcb = pcb_outline()
    inner = round2d(off(pcb, P["clr"]), 1.0)
    outer = round2d(off(pcb, P["clr"] + P["wall"]), P["corner_r"])
    x0, x1 = P["hump_x"]; y0, y1 = P["hump_y"]; hr = P["hump_r"]
    hump = off(box(x0 + hr, -y1 + hr, x1 + 20, -y0 - hr), hr).intersection(outer)
    return pcb, inner, outer, hump


def build(side="left"):
    pcb, inner, outer, hp = outlines()
    zt = Z_BOT + P["tuck_h"]
    shell = loft(outer, tuck(Z_BOT, zt, P["tuck_in"], 16)[:-1]
                 + round_over(Z_DECK - P["top_r"], Z_DECK, P["top_r"], 12))
    rt = P["hump_top"] - P["hump_top_r"]
    shell += loft(hp, [(0.0, 0.0)] + round_over(rt, P["hump_top"], P["hump_top_r"], 12))

    # cavity: full outline down past the sockets, then follows the tuck inward
    cav = [slab(inner, Z_SOCK, P["plate_z"]), slab(off(outer, -P["wall"]), zt, Z_SOCK + 0.01)]
    zs = np.linspace(Z_BOT - 0.01, zt, 24)
    cav += [slab(off(outer, -P["wall"] - tuck_inset(a)), a, b + 0.01) for a, b in zip(zs[:-1], zs[1:])]
    cav.append(slab(off(hp, -P["hump_wall"]).intersection(inner), 0.0, P["hump_top"] - P["hump_wall"]))
    for x, y, r in keys():
        cav.append(cube(x, y, 5, P["key_hole"], P["key_hole"], 20, -r))
    ux, uz, uw, uh = P["usb"]
    usb = Manifold.extrude(cs(rect(0, 0, uw, uh, 2.0)), 12).rotate((90, 0, 0))
    cav.append(usb.translate((ux, -60.0, uz)))
    cav.append(cyl(*xy(*P["reset"]), 0, 30, P["reset_hole"]))
    if side == "left":
        cx, cy, w, h = P["oled_win"]
        cav.append(slab(rect(cx, -cy, w, h, 1.0), 0, 30))
    else:
        cx, cy, w, h = P["pim"]
        cav.append(slab(rect(cx, -cy, w, h, 1.0), P["pim_ledge_z"], 30))
        cav.append(slab(rect(cx, -cy, w - 3, h - 3, 1.0), 0, 30))
    shell -= union(cav)
    # blind screw bosses under the deck: nothing shows on top
    shell += union([cyl(*xy(x, y), 0, P["plate_z"] + 0.01, P["boss_d"]) for x, y in P["screws"]])
    shell -= union([cyl(*xy(x, y), -0.1, Z_DECK - 0.6, P["pilot_d"]) for x, y in P["screws"]])

    # floor
    opening = off(outer, -P["tuck_in"] - P["wall"])
    floor = slab(off(opening, -P["floor_tol"]), Z_BOT, Z_FLOOR)
    floor += union([cyl(*xy(x, y), Z_FLOOR - 0.01, Z_PCB_BOT, P["standoff_d"]) for x, y in P["screws"]])
    bw, bl, bt = P["battery"]; bx, by = P["battery_at"]
    bat = rect(bx, -by, bl + 0.8, bw + 0.8)
    corners = unary_union([Point(c).buffer(7, cap_style="square") for c in bat.exterior.coords[:4]])
    floor += slab(off(bat, 1.2).difference(bat).intersection(corners), Z_FLOOR - 0.01, Z_FLOOR + 2.5)
    holes = [cyl(*xy(x, y), Z_BOT - 1, 40, P["clear_d"]) for x, y in P["screws"]]
    holes += [cyl(*xy(x, y), Z_BOT - 1, Z_BOT + P["head_h"], P["head_d"]) for x, y in P["screws"]]
    mx, my, od, idd, dep = P["magsafe"]
    ringp = Point(mx, -my).buffer(od / 2, 64).difference(Point(mx, -my).buffer(idd / 2, 64))
    holes.append(slab(ringp, Z_BOT - 1, Z_BOT + dep))
    floor -= union(holes)

    # sanity checks
    assert off(opening, -1).contains(off(bat, 1.2)), "battery bay outside floor"
    assert off(opening, -1.5).contains(Point(mx, -my).buffer(od / 2)), "MagSafe ring off the floor"
    for x, y in P["screws"]:
        assert Point(x, -y).distance(bat) > P["standoff_d"] / 2 + 0.5, f"standoff {x},{y} hits battery"
        d = Point(mx, -my).distance(Point(x, -y))
        assert not (idd / 2 - P["head_d"] / 2 - 0.5 < d < od / 2 + P["head_d"] / 2 + 0.5), f"screw {x},{y} on ring"

    if side == "right":
        shell, floor = shell.mirror((1, 0, 0)), floor.mirror((1, 0, 0))
    return shell, floor


def proxies(side="left"):
    """non-printed parts for renders: PCB, switches + keycaps, nano, OLED/PIM447, battery"""
    pcb = slab(pcb_outline(), Z_PCB_BOT, 0)
    cap = Manifold.extrude(cs(rect(0, 0, 17.5, 16.5, 1.2)), 2.6)
    caps = union([cap.rotate((0, 0, -r)).translate((x, y, 6.8)) for x, y, r in keys()])
    misc = [cube(x, y, Z_DECK + 1.2, 15, 15, 2.4, -r) for x, y, r in keys()]
    misc.append(cube(*xy(*P["nano"]), P["nano_z"] + 0.5, 18, 33, 1.0))
    bw, bl, bt = P["battery"]
    misc.append(slab(rect(P["battery_at"][0], -P["battery_at"][1], bl, bw, 1.5), Z_FLOOR, Z_FLOOR + bt))
    if side == "left":
        misc.append(cube(185.1, -87.6, 9.2, 12, 38, 1.6))
    else:
        cx, cy = P["pim"][0], -P["pim"][1]; z = P["pim_ledge_z"]
        misc += [cube(cx, cy, z + 3.25, 22, 25, 6.5), Manifold.sphere(5.5, 48).translate((cx, cy, z + 6.5))]
    out = dict(pcb=pcb, caps=caps, misc=union(misc))
    return {k: v.mirror((1, 0, 0)) for k, v in out.items()} if side == "right" else out


def write_stl(m: Manifold, path: Path):
    mesh = m.to_mesh()
    v = np.asarray(mesh.vert_properties)[:, :3]
    tri = v[np.asarray(mesh.tri_verts)]
    n = np.cross(tri[:, 1] - tri[:, 0], tri[:, 2] - tri[:, 0])
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    rec = np.zeros(len(tri), dtype=[("n", "<f4", 3), ("v", "<f4", (3, 3)), ("a", "<u2")])
    rec["n"], rec["v"] = n, tri
    with open(path, "wb") as f:
        f.write(b"corne-lp-case".ljust(80, b" "))
        f.write(np.uint32(len(tri)).tobytes())
        f.write(rec.tobytes())


if __name__ == "__main__":
    import sys
    models = HERE / "models"; models.mkdir(exist_ok=True)
    preview = HERE / ".preview"; preview.mkdir(exist_ok=True)
    print(f"Z: bottom {Z_BOT:.1f}  floor top {Z_FLOOR:.1f}  PCB 0  deck {Z_DECK:.1f}  hump {P['hump_top']:.1f}\n"
          f"height: keys {Z_DECK - Z_BOT:.1f}  hump {P['hump_top'] - Z_BOT:.1f}  PCB top above desk {-Z_BOT:.1f}")
    for side in sys.argv[1:] or ["left", "right"]:
        shell, floor = build(side)
        write_stl(shell, models / f"{side}_shell.stl")
        write_stl(floor, models / f"{side}_floor.stl")
        for name, part in proxies(side).items():
            write_stl(part, preview / f"{side}_{name}.stl")
        print(side, "shell genus", shell.genus(), "tris", shell.num_tri(), "floor tris", floor.num_tri())
