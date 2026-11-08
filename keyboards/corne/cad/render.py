"""Blender renders of the case. Run after case.py:

  /Applications/Blender.app/Contents/MacOS/Blender -b -P render.py
"""
import math
from pathlib import Path

import bpy
from mathutils import Vector

HERE = Path(__file__).parent
OUT = HERE / "renders"; OUT.mkdir(exist_ok=True)

MATS = {
    "shell": ((0.80, 0.79, 0.75), 0.42),
    "floor": ((0.05, 0.055, 0.06), 0.5),
    "pcb": ((0.02, 0.16, 0.07), 0.45),
    "caps": ((0.42, 0.44, 0.47), 0.65),
    "misc": ((0.08, 0.10, 0.16), 0.4),
}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s = bpy.context.scene
    s.render.engine = "CYCLES"
    prefs = bpy.context.preferences.addons["cycles"].preferences
    try:
        prefs.compute_device_type = "METAL"; prefs.get_devices()
        for d in prefs.devices: d.use = True
        s.cycles.device = "GPU"
    except Exception:
        pass
    s.cycles.samples = 64; s.cycles.use_denoising = True
    s.render.resolution_x, s.render.resolution_y = 1600, 1000
    s.render.film_transparent = False
    s.render.image_settings.file_format = "JPEG"; s.render.image_settings.quality = 85
    s.view_settings.view_transform = "AgX"
    w = bpy.data.worlds.new("w"); s.world = w; w.use_nodes = True
    w.node_tree.nodes["Background"].inputs[0].default_value = (0.86, 0.87, 0.85, 1)
    w.node_tree.nodes["Background"].inputs[1].default_value = 0.6
    return s


def mat(name):
    if name in bpy.data.materials:
        return bpy.data.materials[name]
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    col, rough = MATS[name]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    return m


def load(path, name, dz=0.0):
    bpy.ops.wm.stl_import(filepath=str(path))
    o = bpy.context.selected_objects[0]
    o.data.materials.append(mat(name)); o.location.z += dz
    bpy.ops.object.shade_auto_smooth(angle=math.radians(30))
    return o


def add_half(side, dx=0.0, explode=0.0):
    objs = []
    m, p = HERE / "models", HERE / ".preview"
    objs.append(load(m / f"{side}_shell.stl", "shell", explode * 2))
    objs.append(load(m / f"{side}_floor.stl", "floor"))
    objs.append(load(p / f"{side}_pcb.stl", "pcb", explode))
    objs.append(load(p / f"{side}_caps.stl", "caps", explode * 3))
    objs.append(load(p / f"{side}_misc.stl", "misc", explode))
    # centre on origin
    lo = Vector((min(o.bound_box[i][0] + o.location.x for o in objs[:1] for i in range(8)),
                 min(o.bound_box[i][1] + o.location.y for o in objs[:1] for i in range(8)), 0))
    hi = Vector((max(o.bound_box[i][0] + o.location.x for o in objs[:1] for i in range(8)),
                 max(o.bound_box[i][1] + o.location.y for o in objs[:1] for i in range(8)), 0))
    c = (lo + hi) / 2
    for o in objs:
        o.location.x += dx - c.x; o.location.y -= c.y
    return objs


def lights_and_floor(ground=True):
    for loc, e, size in (((-150, -200, 300), 2.2e6, 250), ((250, 150, 200), 0.8e6, 300), ((0, 300, 60), 0.5e6, 200)):
        l = bpy.data.lights.new("a", "AREA"); l.energy = e; l.size = size
        o = bpy.data.objects.new("a", l); o.location = loc
        o.rotation_euler = (Vector((0, 0, 0)) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
        bpy.context.collection.objects.link(o)
    if ground:
        bpy.ops.mesh.primitive_plane_add(size=3000, location=(0, 0, -11.15))
        g = bpy.context.object; g.is_shadow_catcher = True


def shoot(name, az, el, dist, lens=70, target=(0, 0, 0), ortho=None):
    s = bpy.context.scene
    cd = bpy.data.cameras.new("c"); cd.lens = lens; cd.clip_end = 10000
    if ortho:
        cd.type = "ORTHO"; cd.ortho_scale = ortho
    cam = bpy.data.objects.new("c", cd); bpy.context.collection.objects.link(cam)
    a, e = math.radians(az), math.radians(el)
    t = Vector(target)
    cam.location = t + Vector((dist * math.cos(e) * math.sin(a), -dist * math.cos(e) * math.cos(a), dist * math.sin(e)))
    cam.rotation_euler = (t - cam.location).to_track_quat("-Z", "Y").to_euler()
    s.camera = cam
    s.render.filepath = str(OUT / f"{name}.jpg")
    bpy.ops.render.render(write_still=True)
    print("rendered", name)


# az: 0 = from the front (thumb side), 90 = from the right, 180 = from the back (USB side)
for side in ("left", "right"):
    inner_az = 90 if side == "left" else -90  # controller side
    reset(); add_half(side); lights_and_floor()
    shoot(f"{side}_hero", -30 if side == "left" else 30, 32, 420)
    shoot(f"{side}_back", 180 + (25 if side == "left" else -25), 22, 420)
    shoot(f"{side}_inner", inner_az, 12, 420)
    shoot(f"{side}_outer", -inner_az, 12, 420)
    shoot(f"{side}_front", 0, 6, 420)
    shoot(f"{side}_top", 0, 90, 420, ortho=160)
    shoot(f"{side}_hump", inner_az + (-35 if side == "left" else 35), 35, 200, target=(50 if side == "left" else -50, 0, 6))
    reset(); add_half(side); lights_and_floor(ground=False)
    shoot(f"{side}_bottom", 20, -45, 420)
    reset(); add_half(side, explode=14); lights_and_floor()
    shoot(f"{side}_exploded", -30 if side == "left" else 30, 25, 520)

reset(); add_half("left", dx=-85); add_half("right", dx=85); lights_and_floor()
shoot("pair", 0, 38, 640)
