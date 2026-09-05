"""A second modeling and lighting pass over the five literary Blender studies.

Missing base scenes are built automatically. From the repository root:
blender -b --python art/refine_scenes.py -- --scene matachin --preview
blender -b --python art/refine_scenes.py -- --scene all --final
"""
from pathlib import Path
import argparse
import bisect
import math
import random
import runpy
import sys

import bpy
from mathutils import Vector, Matrix
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parent.parent
BUILD = ROOT / 'build' / 'refinement'
ASSETS = ROOT / 'assets' / 'refinement'
BUILD.mkdir(parents=True, exist_ok=True)
ASSETS.mkdir(parents=True, exist_ok=True)
P = 'Refinement / '
rng = random.Random(9193)


def remove(*prefixes):
    for ob in list(bpy.context.scene.objects):
        if ob.name.startswith(prefixes):
            bpy.data.objects.remove(ob, do_unlink=True)


def mesh(name, vertices, faces, material, smooth=False):
    data = bpy.data.meshes.new(P + name)
    data.from_pydata(vertices, [], faces)
    data.update()
    ob = bpy.data.objects.new(P + name, data)
    bpy.context.scene.collection.objects.link(ob)
    if material:
        data.materials.append(material)
    if smooth:
        for face in data.polygons:
            face.use_smooth = True
    return ob


def weather(name, base, accent=None, scale=2.0, rough=.75, metal=0,
            bump=.25, distance=.025, stretch=(1, 1, 1)):
    """World-scale color variation and fine surface relief, without image maps."""
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.diffuse_color = (*base, 1)
    nodes, links = mat.node_tree.nodes, mat.node_tree.links
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    bs = nodes.new('ShaderNodeBsdfPrincipled')
    links.new(bs.outputs['BSDF'], output.inputs['Surface'])
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Roughness'].default_value = rough
    geo = nodes.new('ShaderNodeNewGeometry')
    stretch_node = nodes.new('ShaderNodeVectorMath')
    stretch_node.operation = 'MULTIPLY'
    stretch_node.inputs[1].default_value = stretch
    links.new(geo.outputs['Position'], stretch_node.inputs[0])
    noise = nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = scale
    noise.inputs['Detail'].default_value = 5
    noise.inputs['Roughness'].default_value = .72
    links.new(stretch_node.outputs['Vector'], noise.inputs['Vector'])
    color = nodes.new('ShaderNodeValToRGB')
    color.color_ramp.elements[0].position = .23
    color.color_ramp.elements[0].color = (*[v * .42 for v in base], 1)
    color.color_ramp.elements[1].position = .79
    color.color_ramp.elements[1].color = (*(accent or [v * 1.25 for v in base]), 1)
    mid = color.color_ramp.elements.new(.52)
    mid.color = (*base, 1)
    links.new(noise.outputs['Fac'], color.inputs[0])
    links.new(color.outputs['Color'], bs.inputs['Base Color'])
    small = nodes.new('ShaderNodeTexNoise')
    small.inputs['Scale'].default_value = scale * 35
    small.inputs['Detail'].default_value = 3
    links.new(stretch_node.outputs['Vector'], small.inputs['Vector'])
    relief = nodes.new('ShaderNodeBump')
    relief.inputs['Strength'].default_value = bump
    relief.inputs['Distance'].default_value = distance
    links.new(small.outputs['Fac'], relief.inputs['Height'])
    links.new(relief.outputs['Normal'], bs.inputs['Normal'])
    rough_map = nodes.new('ShaderNodeMapRange')
    rough_map.inputs['From Min'].default_value = .2
    rough_map.inputs['From Max'].default_value = .8
    rough_map.inputs['To Min'].default_value = max(.08, rough - .15)
    rough_map.inputs['To Max'].default_value = min(1, rough + .12)
    links.new(noise.outputs['Fac'], rough_map.inputs['Value'])
    links.new(rough_map.outputs['Result'], bs.inputs['Roughness'])
    return mat


def plain(name, color, rough=.7, metal=0, emission=0):
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    mat.use_nodes = True
    bs = mat.node_tree.nodes.get('Principled BSDF')
    bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = rough
    bs.inputs['Metallic'].default_value = metal
    bs.inputs['Emission Color'].default_value = (*color, 1)
    bs.inputs['Emission Strength'].default_value = emission
    return mat


def assign(ob, material):
    ob.data.materials.clear()
    ob.data.materials.append(material)


def cube(name, pos, size, material, bevel=.01, rot=None):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pos)
    ob = bpy.context.object
    ob.name = P + name
    ob.dimensions = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if rot:
        ob.rotation_euler = rot
    if bevel:
        mod = ob.modifiers.new('Soft irregular edges', 'BEVEL')
        mod.width, mod.segments = bevel, 2
        ob.modifiers.new('Face normals', 'WEIGHTED_NORMAL')
    assign(ob, material)
    return ob


def tube(name, points, radius, material, closed=False, radii=None):
    data = bpy.data.curves.new(P + name, 'CURVE')
    data.dimensions = '3D'
    data.resolution_u = 8
    data.bevel_depth = radius
    data.bevel_resolution = 2
    spline = data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for i, (p, value) in enumerate(zip(spline.points, points)):
        p.co = (*value, 1)
        if radii:
            p.radius = radii[i]
    spline.use_cyclic_u = closed
    ob = bpy.data.objects.new(P + name, data)
    bpy.context.scene.collection.objects.link(ob)
    data.materials.append(material)
    return ob


def sphere(name, pos, scale, material, segments=24):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=12, location=pos)
    ob = bpy.context.object
    ob.name = P + name
    ob.scale = scale
    assign(ob, material)
    for face in ob.data.polygons:
        face.use_smooth = True
    return ob


class Batch:
    """Collect small modeled details into a few meshes instead of thousands of objects."""
    def __init__(self, materials):
        self.vertices, self.faces, self.indices = [], [], []
        self.materials = materials

    def add(self, vertices, faces, index=0):
        start = len(self.vertices)
        self.vertices.extend(vertices)
        self.faces.extend(tuple(start + v for v in face) for face in faces)
        self.indices.extend([index] * len(faces))

    def box(self, pos, size, index=0, angle=0):
        cx, cy, cz = pos
        sx, sy, sz = [v / 2 for v in size]
        co, si = math.cos(angle), math.sin(angle)
        vertices = [(cx + x * co - y * si, cy + x * si + y * co, cz + z)
                    for z in (-sz, sz) for y in (-sy, sy) for x in (-sx, sx)]
        self.add(vertices, [(0, 2, 3, 1), (4, 5, 7, 6), (0, 1, 5, 4),
                            (2, 6, 7, 3), (0, 4, 6, 2), (1, 3, 7, 5)], index)

    def leaf(self, pos, length, width, azimuth, tilt, index=0, curl=.12):
        center = Vector(pos)
        axis = Vector((math.cos(azimuth) * math.cos(tilt),
                       math.sin(azimuth) * math.cos(tilt), math.sin(tilt)))
        across = Vector((-math.sin(azimuth), math.cos(azimuth), 0))
        vv = [center - axis * length / 2,
              center - axis * length * .1 + across * width / 2,
              center + Vector((0, 0, width * curl)),
              center + axis * length * .48 + Vector((0, 0, -width * curl)),
              center - axis * length * .1 - across * width / 2]
        self.add(vv, [(0, 1, 2), (1, 3, 2), (3, 4, 2), (4, 0, 2)], index)

    def finish(self, name, bevel=0, smooth=False):
        ob = mesh(name, self.vertices, self.faces, None, smooth)
        for mat in self.materials:
            ob.data.materials.append(mat)
        for face, index in zip(ob.data.polygons, self.indices):
            face.material_index = index
        if bevel:
            mod = ob.modifiers.new('Softened details', 'BEVEL')
            mod.width, mod.segments = bevel, 1
        return ob


def relight(world=(.14, .19, .23), strength=.25):
    scene = bpy.context.scene
    for ob in list(scene.objects):
        if ob.type == 'LIGHT':
            bpy.data.objects.remove(ob, do_unlink=True)
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes.get('Background')
    if bg:
        bg.inputs[0].default_value = (*world, 1)
        bg.inputs[1].default_value = strength


def area(name, pos, target, power, size, color):
    data = bpy.data.lights.new(P + name, 'AREA')
    data.energy, data.shape, data.size, data.color = power, 'DISK', size, color
    ob = bpy.data.objects.new(P + name, data)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = pos
    ob.rotation_euler = (Vector(target) - ob.location).to_track_quat('-Z', 'Y').to_euler()
    return ob


def sun_light(name, direction, energy, color, angle=.05):
    data = bpy.data.lights.new(P + name, 'SUN')
    data.energy, data.color, data.angle = energy, color, angle
    ob = bpy.data.objects.new(P + name, data)
    bpy.context.scene.collection.objects.link(ob)
    ob.rotation_euler = Vector(direction).to_track_quat('-Z', 'Y').to_euler()
    return ob


def aim(pos, target, lens=None, ortho=None):
    cam = bpy.context.scene.camera
    cam.location = pos
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat('-Z', 'Y').to_euler()
    if lens:
        cam.data.type, cam.data.lens = 'PERSP', lens
    if ortho:
        cam.data.type, cam.data.ortho_scale = 'ORTHO', ortho
    cam.data.clip_end = 1500
    return cam


def volume(name, pos, size, density, color=(.4, .51, .52)):
    mat = bpy.data.materials.new(P + name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    nodes.clear()
    output = nodes.new('ShaderNodeOutputMaterial')
    scatter = nodes.new('ShaderNodeVolumePrincipled')
    scatter.inputs['Density'].default_value = density
    scatter.inputs['Color'].default_value = (*color, 1)
    scatter.inputs['Anisotropy'].default_value = .25
    mat.node_tree.links.new(scatter.outputs['Volume'], output.inputs['Volume'])
    return cube(name, pos, size, mat, 0)


def distance_haze(color, start=35, depth=130):
    """Fade distant surfaces into the sky using Blender's camera-distance pass."""
    scene = bpy.context.scene
    scene.world.mist_settings.start = start
    scene.world.mist_settings.depth = depth
    scene.world.mist_settings.falloff = 'QUADRATIC'
    scene.view_layers[0].use_pass_mist = True
    graph = bpy.data.node_groups.new(P + 'Distance haze compositor', 'CompositorNodeTree')
    graph.interface.new_socket(name='Image', in_out='OUTPUT', socket_type='NodeSocketColor')
    scene.compositing_node_group = graph
    layers = graph.nodes.new('CompositorNodeRLayers')
    mix = graph.nodes.new('ShaderNodeMix')
    mix.data_type = 'RGBA'
    mix.blend_type = 'MIX'
    mix.inputs[7].default_value = (*color, 1)
    output = graph.nodes.new('NodeGroupOutput')
    graph.links.new(layers.outputs['Mist'], mix.inputs[0])
    graph.links.new(layers.outputs['Image'], mix.inputs[6])
    graph.links.new(mix.outputs[2], output.inputs['Image'])


def matachin():
    scene = bpy.context.scene
    hull = weather('Ancient hull / verdigris', (.022, .078, .085), (.10, .20, .17),
                   scale=2.4, rough=.54, metal=.7, bump=.32, distance=.018, stretch=(1, 1, .23))
    bronze = weather('Exposed worn bronze', (.20, .073, .026), (.30, .17, .055),
                     scale=2, rough=.58, metal=.75, bump=.32, distance=.012)
    iron = weather(P + 'Blackened fittings', (.018, .026, .028), (.065, .071, .058),
                   scale=4, rough=.67, metal=.65, distance=.009)
    old_stone = weather('Basalt and old mortar', (.055, .072, .067), (.19, .19, .14),
                        scale=1.6, rough=.95, distance=.07)
    pavers = [weather(P + 'Paver ' + str(i), (.11 + i * .012, .12 + i * .011, .105 + i * .010),
                       scale=4, rough=.91, bump=.55, distance=.035) for i in range(5)]
    for i in range(4):
        weather('Sandstone ' + str(i), (.19 + i * .013, .18 + i * .011, .126 + i * .012),
                (.32, .32, .25), scale=2.4, bump=.5, distance=.035)
    weather('Dust in the courtyard', (.069, .083, .066), (.135, .146, .11),
            scale=1, rough=.94, bump=.5, distance=.03)
    moss = weather(P + 'Moss in joints', (.03, .057, .023), (.075, .095, .036),
                   scale=8, rough=.95, bump=.6, distance=.016)
    glass = plain(P + 'Rainwater', (.027, .054, .052), .10, .25)
    ground = bpy.data.objects.get('Courtyard ground')
    ground.scale.x = ground.scale.y = 10
    # The worn paving has individual edges and a rough central approach.
    floor = Batch(pavers)
    for j in range(42):
        y = -13 + j * .49
        for i in range(39):
            x = -11 + i * .59 + (j % 2) * .29
            if abs(x) < 1 and -4.5 < y < 1.5:
                continue
            floor.box((x, y, -.004 + rng.uniform(-.01, .015)),
                      (.565 + rng.uniform(-.025, .015), .46, .07), rng.randrange(5), rng.uniform(-.02, .02))
    floor.finish('Individually laid courtyard stones', bevel=.016)
    growth = Batch([moss])
    for k in range(1100):
        x = rng.uniform(-10, 10)
        y = rng.uniform(-8, 7)
        if abs(x) < 1.1:
            continue
        growth.leaf((x, y, .027), rng.uniform(.025, .11), .018,
                    rng.random() * math.tau, rng.uniform(.5, 1.5))
    growth.finish('Grass and moss between stones')
    for x, y, rx, ry in [(-2.3, -6.2, 1.8, .44), (3.1, -3.5, 1.25, .30), (-4.0, -1.7, .6, .25)]:
        boundary = []
        for k in range(60):
            a = math.tau * k / 60
            jitter = 1 + .12 * math.sin(5 * a) + .07 * math.cos(9 * a)
            boundary.append((x + rx * math.cos(a) * jitter, y + ry * math.sin(a) * jitter, .041))
        mesh('Shallow rain pool', boundary, [tuple(range(60))], glass)
    # Raised plate laps, fasteners, and accessible service galleries.
    rivets = Batch([bronze, iron])
    for level in range(15):
        z = .70 + level * .85
        radius = 1.395 - .008 * z
        for k in range(72):
            a = math.tau * k / 72
            rivets.box((radius * math.cos(a), 1.5 + radius * math.sin(a), z),
                       (.035, .055, .04), int(k % 5 == 0), a)
    rivets.finish('Hand-set hull fasteners', bevel=.01)
    for z in (4.02, 8.80, 12.80):
        # Actual narrow ring deck: the tower remains a continuous metal shell.
        verts = []
        for zz, radius in [(z, 1.35), (z, 1.63), (z + .08, 1.63), (z + .08, 1.35)]:
            for k in range(96):
                a = math.tau * k / 96
                verts.append((radius * math.cos(a), 1.5 + radius * math.sin(a), zz))
        faces = []
        for row in range(3):
            for k in range(96):
                faces.append((row * 96 + k, row * 96 + (k + 1) % 96,
                              (row + 1) * 96 + (k + 1) % 96, (row + 1) * 96 + k))
        mesh('Narrow service ring', verts, faces, iron)
        for k in range(28):
            a = math.tau * k / 28
            x, y = 1.57 * math.cos(a), 1.5 + 1.57 * math.sin(a)
            tube('Bent guardrail upright', [(x, y, z + .08), (x, y, z + .60)], .018, iron)
        for height in (.36, .61):
            tube('Guardrail', [(1.57 * math.cos(a), 1.5 + 1.57 * math.sin(a), z + height)
                              for a in [math.tau * k / 160 for k in range(160)]], .022, bronze, True)
    # One ladder and bundled conduits break the manufactured symmetry.
    for x in (-.35, -.02):
        tube('Maintenance ladder rail', [(x, .036, 1.1), (x, .07, 8.65)], .025, iron)
    for k in range(27):
        z = 1.12 + k * .275
        tube('Ladder rung', [(-.37, .02, z), (.00, .02, z)], .025, bronze)
    for k in range(7):
        angle = -.55 + k * .067
        radius = 1.41 + .035 * (k % 2)
        x, y = radius * math.cos(angle), 1.5 + radius * math.sin(angle)
        tube('Oxidized cable bundle', [(x * 1.12, y, .1), (x, y, 2),
                                      (x, y, 6.9), (x * .93, y, 7.2 + k * .11)],
             .021 + (k % 3) * .007, bronze if k % 2 else iron)
    # Missing arch stones and settled piers make the foreground less regular.
    for ob in list(scene.objects):
        if ob.name.startswith('Aged passage / arch stone') and rng.random() < .065:
            ob.location.z -= rng.uniform(.004, .019)
            ob.rotation_euler.y += rng.uniform(-.024, .024)
    chips = Batch(pavers)
    for k in range(130):
        x, y = rng.choice([-1, 1]) * rng.uniform(3.7, 8), rng.uniform(-2.5, 1)
        chips.box((x, y, .09), (rng.uniform(.09, .32), rng.uniform(.08, .23), rng.uniform(.06, .17)),
                  rng.randrange(5), rng.random() * math.tau)
    chips.finish('Settled fragments below the arcade', bevel=.017)
    # Layers of low guild buildings give the vessel an inhabited Citadel around it.
    distant_stone = weather(P + 'Distant guild masonry', (.056, .078, .077), (.105, .133, .12),
                            scale=2, rough=.93, bump=.22, distance=.018)
    distant_roof = weather(P + 'Old roofs in the Citadel', (.032, .049, .05), (.085, .091, .060),
                           scale=3, rough=.78, metal=.25, distance=.013)
    rear_windows = Batch([iron, bronze])
    for layer, y in enumerate((14, 27, 49)):
        for k in range(13):
            x = (k - 6) * (2.4 + layer * .8) + rng.uniform(-.4, .4)
            width = rng.uniform(2.0, 3.4) + layer * .25
            height = rng.uniform(2.6, 5.8) + layer * .75
            depth = rng.uniform(2.2, 3.6)
            cube('Accumulated guild buildings', (x, y, height / 2), (width, depth, height), distant_stone, .035)
            roof_rise = rng.uniform(.38, .9)
            pitched_roof('Weathered Citadel roof', x, y, height, width + .24, depth + .20,
                         roof_rise, distant_roof)
            cube('Old chimney above the roof', (x + width * .22, y + .4, height + roof_rise),
                 (.28, .31, .90), distant_stone, .02)
            if layer < 2:
                for z in range(1, int(height)):
                    for side in (-1, 0, 1):
                        rear_windows.box((x + side * width * .28, y - depth / 2 - .019, z),
                                         (.19, .035, .39), 1 if rng.random() < .016 else 0)
    rear_windows.finish('Recesses in the distant workshops')
    cam = aim((8.2, -25.4, 9.1), (0, 1.5, 7.0), lens=43)
    red_sun = bpy.data.objects['Red sun disc']
    red_sun.location = (4.4, 23, 14.6)
    red_sun.scale = (.82, .82, 1)
    red_sun.rotation_euler = cam.rotation_euler
    assign(red_sun, plain(P + 'A dim red star', (.22, .026, .009), emission=1.0))
    remove('Backdrop')
    relight((.16, .22, .27), .25)
    area('Large cool sky', (-8, -3, 24), (0, 1, 7), 3200, 13, (.58, .77, 1))
    amber = area('Amber grazing light', (8, 7, 19), (0, 1, 6), 3200, 5, (1, .57, .26))
    amber.data.volume_factor = .25
    area('Low courtyard reflection', (1, -10, 4), (0, 1, 4), 320, 8, (.70, .81, .87))
    area('Occupied doorway', (0, -.25, 1.1), (0, -4, .1), 18, .38, (1, .30, .08))
    distance_haze((.026, .038, .046))
    scene['refinement'] = 'Weathered plating, service rings, fasteners, ladders, irregular stone, rain pools, and dusk depth.'


def serpent():
    scene = bpy.context.scene
    blue = weather('Ultramarine / carved stone', (.013, .028, .13), (.022, .049, .18),
                   scale=2.7, rough=.64, metal=.08, bump=.35, distance=.007)
    ramp = next(n for n in blue.node_tree.nodes if n.type == 'VALTORGB')
    ramp.color_ramp.elements[0].color = (.009, .021, .093, 1)
    blue.node_tree.nodes.get('Principled BSDF').inputs['Coat Weight'].default_value = .13
    blue.node_tree.nodes.get('Principled BSDF').inputs['Coat Roughness'].default_value = .37
    body = bpy.data.objects['Serpent / continuous coiled body']
    under_scales = weather(P + 'Dark red between the scales', (.045, .009, .004),
                           (.093, .017, .007), scale=18, rough=.66, distance=.003)
    assign(body, under_scales)
    scale_mats = [weather(P + 'Vermilion scale ' + str(k),
                          (.29 + k * .033, .025 + k * .005, .009 + k * .002),
                          (.46 + k * .025, .064 + k * .007, .018 + k * .003),
                          scale=38, rough=.47 + k * .024, metal=.12, bump=.13, distance=.0015)
                  for k in range(5)]
    # Recover the transported frame of each tube ring from its real mesh.
    vertices = [v.co.copy() for v in body.data.vertices]
    sections = 32
    rings = [vertices[k:k + sections] for k in range(0, len(vertices), sections)]
    centers = [sum(ring, Vector()) / sections for ring in rings]
    radii = [(ring[0] - center).length for ring, center in zip(rings, centers)]
    # Smooth the fitted centerline so tight corners cannot fold the tube into itself.
    anatomy = bpy.data.objects['Blue bust / adapted Lee Perry-Smith anatomical base']
    bvh = BVHTree.FromObject(anatomy, bpy.context.evaluated_depsgraph_get())
    for iteration in range(12):
        relaxed = [centers[0]]
        for i in range(1, len(centers) - 1):
            p = (centers[i - 1] + 2 * centers[i] + centers[i + 1]) * .25
            hit = bvh.find_nearest(p)
            if hit[0] is not None and hit[3] < radii[i] + .026:
                p = hit[0] + hit[1] * (radii[i] + .028)
            relaxed.append(p)
        centers = relaxed + [centers[-1]]
    normals, binormals = [], []
    last_normal = None
    for i, center in enumerate(centers):
        tangent = (centers[min(i + 1, len(centers) - 1)] - centers[max(i - 1, 0)]).normalized()
        normal = tangent.cross(Vector((0, 0, 1))) if last_normal is None else last_normal - tangent * last_normal.dot(tangent)
        if normal.length < .01:
            normal = tangent.cross(Vector((0, 1, 0)))
        normal.normalize()
        binormal = tangent.cross(normal).normalized()
        normals.append(normal)
        binormals.append(binormal)
        last_normal = normal
        for j in range(sections):
            phi = math.tau * j / sections
            body.data.vertices[i * sections + j].co = center + radii[i] * (math.cos(phi) * normal + math.sin(phi) * binormal)
    body.data.update()
    lengths = [0]
    for a, b in zip(centers, centers[1:]):
        lengths.append(lengths[-1] + (b - a).length)

    def surface(arc, phi, lift=0):
        arc = max(0, min(lengths[-1] - .00001, arc))
        index = max(0, min(len(lengths) - 2, bisect.bisect_right(lengths, arc) - 1))
        t = (arc - lengths[index]) / max(.00001, lengths[index + 1] - lengths[index])
        center = centers[index].lerp(centers[index + 1], t)
        normal = normals[index].lerp(normals[index + 1], t).normalized()
        binormal = binormals[index].lerp(binormals[index + 1], t).normalized()
        radius = radii[index] * (1 - t) + radii[index + 1] * t
        return center + (radius + lift) * (math.cos(phi) * normal + math.sin(phi) * binormal)

    scales = Batch(scale_mats)
    columns, pitch = 11, .089
    rows = int((lengths[-1] - .13) / pitch)
    for row in range(rows):
        arc = .13 + row * pitch
        for col in range(columns):
            phi = math.tau * (col + .5 * (row % 2)) / columns
            # Seven vertices give each overlapping shield a subtly convex surface.
            coords = [(arc - .080, phi, .001),
                      (arc - .020, phi - .25, .002),
                      (arc + .042, phi - .23, .003),
                      (arc + .055, phi, .007),
                      (arc + .042, phi + .23, .003),
                      (arc - .020, phi + .25, .002),
                      (arc - .005, phi, .012)]
            vv = [surface(*co) for co in coords]
            scales.add(vv, [(0, 1, 6), (1, 2, 6), (2, 3, 6),
                            (3, 4, 6), (4, 5, 6), (5, 0, 6)], rng.randrange(5))
    scales.finish('Overlapping individually modeled serpent scales', smooth=True)
    head = bpy.data.objects['Serpent / head']
    assign(head, scale_mats[2])
    # Larger head shields follow the ellipsoidal surface.
    head_shields = Batch(scale_mats)
    for row in range(5):
        x = -.58 + row * .27
        for col in range(3):
            y = -.52 + col * .52
            vv = []
            for dx, dy in [(-.14, 0), (0, -.24), (.14, 0), (0, .24), (0, 0)]:
                xx, yy = x + dx, y + dy
                z = math.sqrt(max(.03, 1 - xx * xx - yy * yy)) + (.022 if dx == dy == 0 else .009)
                vv.append(head.matrix_world @ Vector((xx, yy, z)))
            head_shields.add(vv, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], (row + col) % 5)
    head_shields.finish('Broad shields on the serpent head', smooth=True)
    remove('Serpent / head scale')
    wax = bpy.data.materials['Yellow wax'].node_tree.nodes.get('Principled BSDF')
    wax.inputs['Base Color'].default_value = (.78, .42, .018, 1)
    wax.inputs['Emission Strength'].default_value = 0
    wax.inputs['Roughness'].default_value = .28
    wax.inputs['Coat Weight'].default_value = .20
    # Keep the source emblem, with subdued pigment and a small amount of relief.
    decal = bpy.data.materials.get('Heraldic panel / source artwork decal')
    if decal:
        nodes, links = decal.node_tree.nodes, decal.node_tree.links
        bs = nodes.get('Principled BSDF')
        tex = next(n for n in nodes if n.type == 'TEX_IMAGE')
        for link in list(bs.inputs['Emission Color'].links):
            links.remove(link)
        bs.inputs['Emission Strength'].default_value = 0
        bs.inputs['Roughness'].default_value = .43
        bs.inputs['Coat Weight'].default_value = .18
        hue = nodes.new('ShaderNodeHueSaturation')
        hue.inputs['Saturation'].default_value = .97
        hue.inputs['Value'].default_value = .95
        links.new(tex.outputs['Color'], hue.inputs['Color'])
        links.new(hue.outputs['Color'], bs.inputs['Base Color'])
        relief = nodes.new('ShaderNodeBump')
        relief.inputs['Strength'].default_value = .20
        relief.inputs['Distance'].default_value = .005
        links.new(tex.outputs['Color'], relief.inputs['Height'])
        links.new(relief.outputs['Normal'], bs.inputs['Normal'])
    for node in scene.world.node_tree.nodes:
        if node.type == 'BACKGROUND' and node.name != 'Background':
            node.inputs[0].default_value = (.70, .49, .105, 1)
            node.inputs[1].default_value = 1
    aim((2.7, -16, 1.1), (0, 0, .73), ortho=3.04)
    relight((.45, .52, .64), .18)
    area('Warm raking studio light', (-4.0, -5.5, 5.5), (0, 0, .7), 700, 3.4, (.96, .91, .78))
    area('Cool shadow fill', (4, -4, 1.4), (0, 0, .3), 80, 4, (.45, .64, 1))
    area('Thin warm edge', (-1, 1.5, 4.5), (0, 0, 1.0), 460, 2.1, (1, .65, .31))
    scene.view_settings.view_transform = 'Standard'
    scene.view_settings.look = 'None'
    scene.view_settings.exposure = -.20
    scene['refinement'] = 'Modeled overlapping scales, pigment variation, fine stone texture, wax highlights, and restrained studio lighting.'


def casa():
    scene = bpy.context.scene
    plaster = weather('Weathered adobe', (.27, .185, .103), (.43, .32, .19),
                      scale=.7, rough=.95, bump=.34, distance=.015)
    weather('Patches of old plaster', (.40, .325, .213), (.59, .49, .33),
            scale=1.5, rough=.98, bump=.3, distance=.012)
    wood = weather('Warped old boards', (.043, .026, .013), (.15, .098, .040),
                   scale=3, rough=.88, bump=.55, distance=.017, stretch=(18, .5, 12))
    weather('Old roof tiles', (.21, .063, .024), (.35, .14, .054),
            scale=3.2, rough=.85, bump=.38, distance=.01)
    weather('Dull mortar', (.13, .136, .105), (.23, .235, .16),
            scale=.9, rough=.83, bump=.45, distance=.013)
    weather('Oranges in the courtyard', (.59, .145, .008), (.82, .31, .02),
            scale=15, rough=.48, bump=.22, distance=.003)
    dark = plain('Unlit cells', (.005, .006, .004), .97)
    iron = weather('Rusty nails and rails', (.03, .021, .012), (.105, .047, .013),
                   scale=12, rough=.7, metal=.55, distance=.009)
    exposed = weather(P + 'Adobe under the limewash', (.21, .11, .057), (.34, .19, .085),
                      scale=3.5, rough=.99, bump=.7, distance=.025)
    leaves = [weather(P + 'Living orange leaf ' + str(k),
                      (.016 + k * .006, .037 + k * .012, .009 + k * .004),
                      (.065 + k * .007, .12 + k * .009, .023),
                      scale=40, rough=.48 + k * .04, bump=.12, distance=.002)
              for k in range(5)]
    dry_leaf = plain(P + 'Fallen dry leaves', (.145, .074, .022), .96)
    # Replace the smooth canopy masses with branching twigs and individual leaves.
    branch_ends = [tuple(ob.data.splines[0].points[-1].co[:3]) for ob in scene.objects
                   if ob.name.startswith('Twisted branches')]
    remove('Dense orange leaves')
    foliage = Batch(leaves)
    for end in branch_ends:
        end = Vector(end)
        for k in range(14):
            azimuth = rng.random() * math.tau
            reach = rng.uniform(.22, .53)
            tip = end + Vector((math.cos(azimuth) * reach, math.sin(azimuth) * reach,
                                rng.uniform(-.19, .38)))
            mid = end.lerp(tip, .5) + Vector((0, 0, .055))
            tube('Fine orange-tree twig', [end, mid, tip], .0085, wood, radii=[1, .65, .10])
            for j in range(16):
                t = .15 + j * .85 / 16
                center = end.lerp(tip, t) + Vector((rng.uniform(-.025, .025), rng.uniform(-.025, .025), .025))
                direction = azimuth + (-1 if j % 2 else 1) * rng.uniform(.6, 1.4)
                foliage.leaf(center, rng.uniform(.17, .26), rng.uniform(.055, .09), direction,
                             rng.uniform(-.5, .75), rng.randrange(len(leaves)), curl=.18)
    foliage.finish('Individual orange leaves')
    litter = Batch([dry_leaf, leaves[0]])
    for k in range(180):
        pos = (-.7 + rng.gauss(0, 1.2), .5 + rng.gauss(0, 1.1), .041)
        litter.leaf(pos, rng.uniform(.06, .14), .035, rng.random() * math.tau,
                    rng.uniform(-.05, .14), 0 if k % 5 else 1, curl=.25)
    litter.finish('Dry leaves in the court')
    remove('Flaked plaster', 'Cloth-wrapped clutter', 'Bundle cord')
    paving_mats = [weather(P + 'Quiet courtyard stone ' + str(k), color,
                          scale=.7, rough=.88, bump=.35, distance=.015)
                   for k, color in enumerate([(.17, .17, .125), (.18, .165, .117),
                                               (.15, .17, .137), (.19, .18, .13)])]
    for ob in scene.objects:
        if ob.name.startswith('Uneven paving'):
            assign(ob, rng.choice(paving_mats))
    # Narrow planks replace the unbroken gallery floor.
    remove('Upper gallery')
    deck = Batch([wood])
    for side in (-1, 1):
        for k in range(49):
            y = -4.15 + k * .175
            if side == -1 and k in (12, 13, 28):
                continue
            deck.box((side * 3.50, y, 3.14 + rng.uniform(-.018, .016)),
                     (1.36 + rng.uniform(-.08, .03), .16, .105), angle=rng.uniform(-.012, .012))
    deck.finish('Worn gallery floorboards', bevel=.006)
    # An actual staircase connects the court to the left gallery.
    for k in range(18):
        y, z = -3.58 + k * .19, .14 + k * .172
        cube('Worn stair tread', (-3.45, y, z), (1.17, .26, .075), wood, .017)
        if k % 3 == 0:
            tube('Stair baluster', [(-2.88, y, z), (-2.88, y, z + .76)], .027, wood)
    for x in (-3.96, -2.92):
        tube('Stair stringer', [(x, -3.72, .04), (x, -.27, 3.01)], .070, wood)
    tube('Polished stair handrail', [(-2.88, -3.60, .90), (-2.88, -.25, 3.94)], .040, wood)
    # Dark jambs and lintels put the shuttered openings into the wall.
    joinery = Batch([wood, iron])
    for side in (-1, 1):
        for j in range(6):
            y = -3.6 + j * 1.31
            for yy in (y - .40, y + .40):
                joinery.box((side * 3.973, yy, 1.13), (.115, .075, 2.19))
            joinery.box((side * 3.969, y, 2.235), (.14, .92, .13))
            for z in (.75, 1.50, 2.02):
                for yy in (y - .28, y + .28):
                    joinery.box((side * 3.967, yy, z), (.025, .023, .023), 1)
            joinery.box((side * 3.977, y, 4.00), (.21, .87, .065))
    joinery.finish('Door frames, hinges and weathered lintels', bevel=.008)
    # Expose real thickness at three rear doorways instead of flat black rectangles.
    cutters = Batch([dark])
    door_x = [-3.5 + j * 1.17 for j in (1, 3, 5)]
    for x in door_x:
        cutters.box((x, 4.3, 1.08), (.73, 1.5, 2.18))
    cutter = cutters.finish('Doorway cutting volumes')
    wall = bpy.data.objects['Back wing']
    boolean = wall.modifiers.new('Open doorways through the adobe', 'BOOLEAN')
    boolean.operation, boolean.solver, boolean.object = 'DIFFERENCE', 'EXACT', cutter
    bpy.context.view_layer.objects.active = wall
    bpy.ops.object.modifier_apply(modifier=boolean.name)
    bpy.data.objects.remove(cutter, do_unlink=True)
    for ob in list(scene.objects):
        if ob.name.startswith('Rear cell door') and any(abs(ob.location.x - x) < .1 for x in door_x):
            bpy.data.objects.remove(ob, do_unlink=True)
    cube('Unlit passage beyond the rear doors', (0, 5.9, 1.3), (8.5, .15, 2.6), dark)
    cube('Rear passage ceiling', (0, 5, 2.6), (8.6, 2, .12), wood)
    # Broad areas of missing plaster expose brick-sized adobe beneath it.
    bricks = Batch([exposed])
    for x0, z0, rx, rz in [(-2.7, 2.70, .85, .55), (2.65, 3.26, 1.02, .52), (.25, 5.55, 1.0, .37)]:
        for row in range(7):
            z = z0 - rz + row * .18
            for col in range(9):
                x = x0 - rx + col * .255 + (row % 2) * .11
                if ((x - x0) / rx)**2 + ((z - z0) / rz)**2 < rng.uniform(.70, 1.15):
                    bricks.box((x, 3.941, z), (.231, .025, .149), angle=rng.uniform(-.008, .008))
    bricks.finish('Exposed adobe beneath flaking plaster', bevel=.009)
    for k in range(14):
        x0, z0 = rng.uniform(-4.1, 4.1), rng.uniform(2.4, 6)
        points = [(x0 + .05 * math.sin(i * 1.7 + k), 3.927, z0 - i * .10) for i in range(rng.randrange(3, 8))]
        tube('Settled plaster crack', points, .008, exposed)
    # A small basin catches the last daylight in a dark corner.
    basin = sphere('Old wash basin', (2.68, -.95, .14), (.49, .36, .18), iron)
    rim = [(2.68 + .49 * math.cos(a), -.95 + .36 * math.sin(a), .24)
           for a in [math.tau * k / 80 for k in range(80)]]
    tube('Rolled basin lip', rim, .025, iron, True)
    water = plain(P + 'Still water in basin', (.025, .043, .035), .12, .25)
    sphere('Basin water', (2.68, -.95, .241), (.43, .30, .006), water)
    aim((1.7, -8.2, 3.1), (-.25, 1.15, 2.8), lens=32)
    relight((.18, .24, .29), .18)
    area('Open sky above the court', (0, 1, 12), (0, 1, 0), 1400, 10, (.60, .75, 1))
    sun_light('Late sun over the broken roof', (1.0, 1.2, -1.65), 2.5, (1, .69, .38), .04)
    area('Warm room behind the boards', (.01, 5.15, 1.25), (.01, 2, .8), 18, .4, (1, .31, .08))
    area('Soft entrance bounce', (0, -5, 4), (0, 1, 2), 180, 5, (.87, .83, .69))
    volume('Dust in the last light', (0, 1, 4), (9, 10, 9), .007, (.54, .47, .32))
    scene['refinement'] = 'Individual leaves and twigs, worn gallery planks and stairs, open doorways, damaged plaster, and a view from within the courtyard.'


def pitched_roof(name, x, y, z, width, depth, rise, material):
    verts = [(x - width / 2, y - depth / 2, z), (x, y - depth / 2, z + rise),
             (x + width / 2, y - depth / 2, z), (x - width / 2, y + depth / 2, z),
             (x, y + depth / 2, z + rise), (x + width / 2, y + depth / 2, z)]
    return mesh(name, verts, [(0, 1, 2), (3, 5, 4), (0, 3, 4, 1), (1, 4, 5, 2)], material)


def combray():
    scene = bpy.context.scene
    ivory = weather('Ivory porcelain', (.74, .69, .54), (.85, .79, .62),
                    scale=4, rough=.20, bump=.05, distance=.001)
    porcelain_bs = ivory.node_tree.nodes.get('Principled BSDF')
    for link in list(porcelain_bs.inputs['Base Color'].links):
        ivory.node_tree.links.remove(link)
    porcelain_bs.inputs['Base Color'].default_value = (.74, .69, .54, 1)
    porcelain_bs.inputs['Coat Weight'].default_value = .27
    blue = weather('Cobalt china line', (.009, .027, .073), (.016, .06, .15),
                   scale=9, rough=.30, distance=.001)
    wood = weather('Walnut tabletop', (.060, .028, .010), (.145, .069, .024),
                   scale=2, rough=.55, bump=.22, distance=.006, stretch=(.4, 22, 4))
    stone = weather('Combray / pale remembered stone', (.42, .385, .29), (.60, .56, .43),
                    scale=7, rough=.84, bump=.36, distance=.005)
    slate = weather('Slate roofs', (.020, .055, .073), (.087, .125, .13),
                    scale=16, rough=.63, bump=.22, distance=.003)
    gold = weather('Fine gilding', (.55, .33, .09), (.75, .50, .19),
                   scale=10, rough=.24, metal=.80, distance=.001)
    dark = plain(P + 'Tiny window recesses', (.008, .013, .014), .88)
    warm = plain(P + 'A lit remembered room', (.61, .26, .060), .66, emission=.20)
    tea = weather('Lime-flower tea', (.09, .033, .008), (.25, .105, .022),
                  scale=6, rough=.12, metal=.12, bump=.04, distance=.0007)
    bs = tea.node_tree.nodes.get('Principled BSDF')
    bs.inputs['IOR'].default_value = 1.333
    bs.inputs['Coat Weight'].default_value = .30
    # The little church has a nave, buttresses, a belfry and a clock face.
    remove('Parish church tower', 'Church spire', 'Belfry', 'Church cross', 'Cross arm')
    tx, ty, base, tower_h = -.16, .14, 1.22, 1.71
    cube('Saint-Hilaire tower', (tx, ty, base + tower_h / 2), (.48, .46, tower_h), stone, .007)
    cube('Church nave', (tx + .31, ty + .48, base + .33), (.66, .84, .66), stone, .006)
    pitched_roof('Church nave roof', tx + .31, ty + .48, base + .65, .78, .95, .36, slate)
    # Steep, four-sided roof, capped with a very small cross.
    verts = [(tx - .35, ty - .34, base + tower_h), (tx + .35, ty - .34, base + tower_h),
             (tx + .35, ty + .34, base + tower_h), (tx - .35, ty + .34, base + tower_h),
             (tx, ty, base + tower_h + .72)]
    mesh('Church tower roof', verts, [(0, 1, 4), (1, 2, 4), (2, 3, 4), (3, 0, 4)], slate)
    for side in (-1, 1):
        for yy in (-.28, .13, .55):
            cube('Church buttress', (tx + .31 + side * .38, ty + .48 + yy, base + .29),
                 (.08, .10, .61), stone, .003)
    for x in (tx - .12, tx + .12):
        cube('Belfry recess', (x, ty - .235, 2.59), (.12, .025, .30), dark, .025)
        for k in range(6):
            cube('Belfry louvre', (x, ty - .258, 2.47 + k * .044), (.113, .022, .015), slate, .001)
    dial = sphere('Small church clock', (tx, ty - .246, 2.20), (.106, .015, .106), ivory)
    for k in range(12):
        a = math.tau * k / 12
        tube('Clock hour mark', [(tx + .080 * math.sin(a), ty - .264, 2.20 + .080 * math.cos(a)),
                                  (tx + .093 * math.sin(a), ty - .264, 2.20 + .093 * math.cos(a))], .0032, dark)
    tube('Clock hands', [(tx - .060, ty - .267, 2.235), (tx, ty - .267, 2.20),
                         (tx + .018, ty - .267, 2.269)], .004, dark)
    for zz in (1.58, 2.00, 2.82):
        cube('Tower string course', (tx, ty, zz), (.505, .485, .037), ivory, .003)
    tube('Church cross', [(tx, ty, 3.63), (tx, ty, 3.87)], .009, gold)
    tube('Cross arm', [(tx - .073, ty, 3.79), (tx + .073, ty, 3.79)], .008, gold)
    # Quiet architectural detail gives each house its own face.
    houses = [ob for ob in scene.objects if ob.name.startswith('A remembered house')]
    shutters = Batch([slate, dark, stone, warm])
    roof_tiles = Batch([slate])
    for index, ob in enumerate(houses):
        x, y, z = ob.location
        width, depth, height = ob.dimensions
        for wx in (x - width * .23, x + width * .23):
            for wz in (1.42, 1.73):
                shutters.box((wx, y - depth / 2 - .024, wz), (.050, .012, .091), 3 if index % 4 == 0 else 1)
                for side in (-1, 1):
                    shutters.box((wx + side * .050, y - depth / 2 - .024, wz), (.020, .019, .13), 0)
                shutters.box((wx, y - depth / 2 - .031, wz), (.008, .010, .093), 2)
        shutters.box((x, y - depth / 2 - .023, 1.33), (.078, .017, .18), 1)
        top = z + height / 2
        cube('Brick chimney', (x + width * .22, y + depth * .15, top + .22), (.058, .057, .30), stone, .003)
        cube('Chimney pot', (x + width * .22, y + depth * .15, top + .389), (.071, .069, .035), slate, .002)
        for row in range(8):
            yy = y - depth * .61 + row * depth * 1.22 / 8
            for side in (-1, 1):
                for col in range(6):
                    t0, t1 = col / 6, min(1, (col + .95) / 6)
                    xa, xb = x + side * width * .58 * t0, x + side * width * .58 * t1
                    za, zb = top + .30 * (1 - t0) + .008, top + .30 * (1 - t1) + .008
                    roof_tiles.add([(xa, yy, za), (xb, yy, zb), (xb, yy + depth * .145, zb),
                                    (xa, yy + depth * .145, za)], [(0, 1, 2, 3)])
    shutters.finish('Tiny shutters, mullions and doorways', bevel=.001)
    roof_tiles.finish('Overlapping miniature slate tiles')
    # Replace topiary blobs with airy miniature trees and garden foliage.
    garden_positions = [ob.location.copy() for ob in scene.objects if ob.name.startswith('Combray gardens')]
    remove('Combray gardens')
    garden_colors = [plain(P + 'Garden greens ' + str(k), (.027 + k * .012, .063 + k * .017, .014 + k * .008), .84)
                     for k in range(4)]
    garden = Batch(garden_colors)
    for center in garden_positions:
        tube('Miniature tree trunk', [(center.x, center.y, 1.22), (center.x, center.y, 1.57)], .013, wood)
        for k in range(70):
            pos = center + Vector((rng.gauss(0, .095), rng.gauss(0, .085), .12 + rng.gauss(0, .11)))
            garden.leaf(pos, rng.uniform(.045, .085), .025, rng.random() * math.tau,
                        rng.uniform(-.8, .8), rng.randrange(4))
    garden.finish('Small leaves in the remembered gardens')
    # A shell-shaped cake with volume, a browned edge, and fine crumb pores.
    remove('Scallop-shell madeleine')
    cake = weather('Madeleine / baked shell', (.39, .155, .022), (.72, .39, .095),
                   scale=12, rough=.79, bump=.65, distance=.006)
    vv, ff = [], []
    rows, cols = 70, 64
    for j in range(rows + 1):
        t = j / rows
        radius = .075 + .49 * math.sin(math.pi * t)**.63
        for i in range(cols + 1):
            a = -math.pi / 2 + math.pi * i / cols
            ridge = .027 * math.cos(a * 16) * math.sin(math.pi * t)
            x = -1.36 + radius * math.sin(a)
            y = -2.48 + 1.46 * t
            z = .018 + .34 * math.sin(math.pi * t)**.7 * max(0, math.cos(a))**1.1 + ridge
            vv.append((x, y, max(.016, z)))
    for j in range(rows):
        for i in range(cols):
            v = j * (cols + 1) + i
            ff.append((v, v + 1, v + cols + 2, v + cols + 1))
    cake_ob = mesh('A plump fluted madeleine', vv, ff, cake, True)
    solid = cake_ob.modifiers.new('Baked underside', 'SOLIDIFY')
    solid.thickness = .035
    # A tarnished spoon and a folded cloth make this feel like an ordinary table.
    silver = weather(P + 'Tarnished silver', (.22, .21, .17), (.63, .61, .49),
                     scale=14, rough=.29, metal=.91, bump=.1, distance=.001)
    bowl = sphere('Teaspoon bowl', (1.96, -1.71, .057), (.17, .31, .032), silver)
    bowl.rotation_euler.z = -.42
    tube('Teaspoon handle', [(2.08, -1.46, .07), (2.19, -1.05, .052),
                            (2.38, -.40, .027)], .031, silver)
    sphere('Spoon handle end', (2.39, -.37, .029), (.057, .12, .023), silver)
    linen = weather(P + 'Unbleached linen', (.40, .365, .28), (.58, .54, .43),
                    scale=25, rough=.98, bump=.46, distance=.002, stretch=(1, 1.4, 1))
    cloth_v, cloth_f = [], []
    nx, ny = 45, 38
    for j in range(ny + 1):
        for i in range(nx + 1):
            x, y = .50 + i * 2.25 / nx, -2.98 + j * .91 / ny
            z = .010 + .035 * math.sin(i * .39) * math.sin(math.pi * j / ny)**2
            z += .021 * math.sin(j * .65 + i * .12)**2
            cloth_v.append((x, y, z))
    for j in range(ny):
        for i in range(nx):
            v = j * (nx + 1) + i
            cloth_f.append((v, v + 1, v + nx + 2, v + nx + 1))
    mesh('A folded linen napkin', cloth_v, cloth_f, linen, True)
    # Very fine floral strokes beneath the rim of the china.
    for k in range(24):
        a = math.tau * k / 24
        points = []
        for j in range(16):
            t = j / 15
            phi = a + .024 * math.sin(math.pi * t)
            zz = 1.18 - .30 * t
            rr = 1.2 + (zz - .85) * .30 + .004
            points.append((rr * math.cos(phi), rr * math.sin(phi), zz))
        tube('Hand-painted china sprig', points, .0045, blue)
        for sign in (-1, 1):
            tube('Painted leaf stroke', [(1.264 * math.cos(a), 1.264 * math.sin(a), 1.05),
                                         (1.273 * math.cos(a + sign * .020), 1.273 * math.sin(a + sign * .020), 1.08)], .006, blue)
    camera = aim((5.2, -10.8, 5.7), (0, 0, 1.75), lens=69)
    camera.data.dof.use_dof = True
    camera.data.dof.focus_distance = (Vector((0, 0, 1.7)) - camera.location).length
    camera.data.dof.aperture_fstop = 7.1
    relight((.24, .27, .30), .18)
    area('Large morning window', (-4.0, -1.2, 7), (0, 0, 1), 630, 3.3, (1, .80, .54))
    area('Cool reflected room light', (4, -3, 3), (0, 0, 1), 90, 5, (.56, .72, 1))
    # A window frame casts the quiet pattern of a real morning on the table.
    sun_light('Low sun through the room', (.6, .8, -1.4), 1.2, (1, .82, .56), .10)
    scene['refinement'] = 'A more complete miniature church and village, slate roofs, tiny windows, foliage, porcelain detail, linen, and a baked madeleine.'


def shore():
    scene = bpy.context.scene
    remove('Surface of the sea', 'Thin breaking wave', 'Broken foam line', 'Foam fleck',
           'A dark band left by a wave', 'Distant atmospheric field', 'Sand and pebbles',
           'Loose neck cord')
    sand = weather('Sacred sand', (.17, .127, .071), (.30, .23, .13),
                   scale=3, rough=.85, bump=.70, distance=.004)
    wet = weather('Wet sand', (.08, .075, .044), (.18, .143, .074),
                  scale=4, rough=.29, metal=.05, bump=.4, distance=.0017)
    water = weather('Evening sea', (.009, .042, .045), (.021, .085, .089),
                    scale=9, rough=.16, metal=.06, bump=.22, distance=.009,
                    stretch=(.7, 1.9, .5))
    water_bs = water.node_tree.nodes.get('Principled BSDF')
    water_bs.inputs['IOR'].default_value = 1.333
    water_bs.inputs['Coat Weight'].default_value = .19
    water_bs.inputs['Transmission Weight'].default_value = .035
    foam = weather('Lace of foam', (.32, .39, .32), (.59, .64, .49),
                   scale=30, rough=.79, bump=.36, distance=.002)
    leather = weather('Travelled leather', (.018, .013, .007), (.078, .045, .014),
                      scale=14, rough=.68, bump=.43, distance=.004)
    boots = sorted([ob for ob in scene.objects if ob.name.startswith('Boot in the waves')], key=lambda ob: ob.name)
    for ob, pos, rot in zip(boots, [(1.45, 1.5, .020), (2.24, 2.05, .027)],
                           [(.12, 1.32, .45), (.28, -1.40, -.60)]):
        ob.location = pos
        ob.rotation_euler = rot
    bark = weather('Curved thorn', (.021, .016, .009), (.10, .068, .028),
                   scale=15, rough=.70, bump=.55, distance=.006, stretch=(.5, 9, 9))
    cord = weather('Worn cord', (.21, .135, .054), (.37, .27, .125),
                   scale=70, rough=.92, bump=.3, distance=.0005)
    pebble_mats = [weather(P + 'Shore pebble ' + str(k), color, scale=20, rough=.43,
                           bump=.22, distance=.001)
                   for k, color in enumerate([(.069, .076, .055), (.11, .064, .029),
                                               (.15, .14, .094), (.028, .044, .042)])]
    remove('Beach')
    # Carry the sea all the way to the horizon beyond the detailed wave mesh.
    cube('Distant sea below the wind ripples', (0, 2520, -.15), (6000, 5000, .01), water, 0)

    def shoreline(x):
        return -.1 + .26 * math.sin(x * .31) + .085 * math.sin(x * 1.23)

    def sea_height(x, y):
        distance = y - shoreline(x)
        amp = min(1, max(0, distance / .8))
        return .006 + amp * (.028 * math.sin(x * 1.1 + y * 2.5)
                             + .011 * math.sin(x * 2.3 - y * 3.1)
                             + .005 * math.sin(x * 8.2 + y * 7.3))

    # A dense near shore and a gradually coarser distant sea avoid repeated stripes.
    vv, ff = [], []
    nx, ny = 360, 360
    for j in range(ny + 1):
        offset = 1.3 * (math.exp(4.85 * j / ny) - 1)
        for i in range(nx + 1):
            x = -48 + i * 96 / nx
            y = shoreline(x) + offset
            vv.append((x, y, sea_height(x, y)))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            ff.append((a, a + 1, a + nx + 2, a + nx + 1))
    mesh('Crossing wind ripples on the sea', vv, ff, water, True)
    # A low, irregular beach with footprints gently pressed into the damp sand.
    footprints = []
    for k in range(9):
        y = -5.6 + k * .58
        x = .54 + .14 * math.sin(k * .55) + (.15 if k % 2 else -.15)
        footprints.append((x, y))
    vv, ff = [], []
    nx, ny = 340, 250
    for j in range(ny + 1):
        y = -15 + j * 15.65 / ny
        for i in range(nx + 1):
            t = -1 + 2 * i / nx
            x = 22 * math.copysign(abs(t)**1.8, t)
            z = -.052 + .009 * math.sin(x * .7 + y * .3) + .004 * math.sin(3.4 * x - y * 1.2)
            for px, py in footprints:
                z -= .025 * math.exp(-((x - px) / .075)**4 - ((y - py) / .21)**4)
                z -= .018 * math.exp(-((x - px) / .058)**2 - ((y - py + .20) / .075)**2)
            vv.append((x, y, z))
    for j in range(ny):
        for i in range(nx):
            a = j * (nx + 1) + i
            ff.append((a, a + 1, a + nx + 2, a + nx + 1))
    ground = mesh('Sand with shallow footprints', vv, ff, sand, True)
    ground.data.materials.append(wet)
    for face in ground.data.polygons:
        # The tidal band is wet, with a softly irregular boundary.
        center = sum((ground.data.vertices[k].co for k in face.vertices), Vector()) / len(face.vertices)
        if center.y > shoreline(center.x) - 1.65 - .15 * math.sin(center.x * 2.2):
            face.material_index = 1
    # Broken foam strands have changing widths and irregular gaps.
    foam_mesh = Batch([foam])
    for row in range(3):
        for k in range(60):
            x0 = -12 + k * .4 + rng.uniform(-.12, .12)
            if rng.random() < (.13 if row == 0 else .46):
                continue
            length = rng.uniform(.14, .46)
            offset = [.018, .65, 1.8][row]
            points = []
            for j in range(13):
                x = x0 + length * j / 12
                y = shoreline(x) + offset + .033 * math.sin(x * 9.8 + row) + .025 * math.sin(x * 21.5)
                points.append((x, y, sea_height(x, y) + .009))
            tube('Fragments of receding foam', points, [.011, .007, .005][row], foam)
            for j in range(8):
                x = x0 + rng.random() * length
                y = shoreline(x) + offset + rng.uniform(.01, .17)
                radius = rng.uniform(.005, .024)
                z = sea_height(x, y) + .007
                poly = [(x + radius * math.cos(a), y + radius * 1.8 * math.sin(a), z)
                        for a in [math.tau * n / 7 for n in range(7)]]
                foam_mesh.add(poly, [tuple(range(7))])
    foam_mesh.finish('Small patches of sea foam')
    # Lay the thorn and its cord on the sand, close enough to the lens to read.
    original = Vector((-1.5, -5.1, .02))
    destination = Vector((-.63, -4.68, -.023))
    rotation = Matrix.Rotation(math.radians(-22), 4, 'Z') @ Matrix.Rotation(math.radians(84), 4, 'X')
    for ob in scene.objects:
        if ob.name.startswith('The curved thorn'):
            for vertex in ob.data.vertices:
                vertex.co = destination + .12 * (rotation.to_3x3() @ (vertex.co - original))
        elif ob.name.startswith('Cord tied around the thorn'):
            for spline in ob.data.splines:
                for point in spline.points:
                    co = destination + .12 * (rotation.to_3x3() @ (Vector(point.co[:3]) - original))
                    point.co = (*co, 1)
            ob.data.bevel_depth *= .12
    necklace = []
    for k in range(151):
        a = math.tau * k / 150
        x = -.72 + .32 * math.cos(a) + .04 * math.sin(a * 3)
        y = -4.98 + .37 * math.sin(a)
        z = -.023 + .008 * math.sin(a * 2)
        necklace.append((x, y, z))
    tube('Loose cord on the sand', necklace, .0035, cord, True)
    for k in range(100):
        x, y = rng.uniform(-5, 5), rng.uniform(-6.8, -.6)
        size = rng.uniform(.009, .045)
        ob = sphere('A rounded beach pebble', (x, y, -.028), (size, size * 1.32, size * .35),
                    rng.choice(pebble_mats), segments=24)
        ob.rotation_euler.z = rng.random() * math.tau
    # A little split shell catches the grazing light in the foreground.
    shell = plain(P + 'Old shell', (.30, .28, .19), .68)
    shell_v, shell_f = [], []
    for row in range(8):
        r = .011 + row * .011
        for col in range(20):
            a = math.pi * col / 19
            shell_v.append((-.20 + r * math.cos(a), -4.53 + r * math.sin(a),
                            -.024 + .042 * math.sin(row / 7 * math.pi / 2) + .003 * math.cos(a * 9)))
    for row in range(7):
        for col in range(19):
            i = row * 20 + col
            shell_f.append((i, i + 1, i + 21, i + 20))
    mesh('A broken scallop shell', shell_v, shell_f, shell, True)
    cam = aim((.20, -8.2, 1.4), (.8, 4, -.1), lens=36)
    cam.data.dof.use_dof = True
    cam.data.dof.focus_distance = 5.0
    cam.data.dof.aperture_fstop = 11
    sun = bpy.data.objects['Last red sun']
    sun.location = (-11, 90, 4.2)
    sun.scale = (2.5, 2.5, 1)
    sun.rotation_euler = cam.rotation_euler
    assign(sun, plain(P + 'Sun through sea haze', (.32, .059, .017), emission=1.8))
    relight((.17, .28, .32), .44)
    # A restrained horizon gradient; no visible backdrop plane or hard rectangular edge.
    nodes, links = scene.world.node_tree.nodes, scene.world.node_tree.links
    bg = nodes.get('Background')
    tex = nodes.new('ShaderNodeTexCoord')
    sep = nodes.new('ShaderNodeSeparateXYZ')
    mapping = nodes.new('ShaderNodeMapRange')
    mapping.inputs['From Min'].default_value = -.02
    mapping.inputs['From Max'].default_value = .50
    mapping.inputs['To Min'].default_value = 0
    mapping.inputs['To Max'].default_value = 1
    ramp = nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (.16, .24, .235, 1)
    ramp.color_ramp.elements[1].color = (.025, .073, .13, 1)
    links.new(tex.outputs['Normal'], sep.inputs[0])
    invert = nodes.new('ShaderNodeMath')
    invert.operation = 'MULTIPLY'
    invert.inputs[1].default_value = -1
    links.new(sep.outputs['Z'], invert.inputs[0])
    links.new(invert.outputs[0], mapping.inputs['Value'])
    links.new(mapping.outputs['Result'], ramp.inputs[0])
    links.new(ramp.outputs['Color'], bg.inputs[0])
    sky_light = area('Broad cool sky', (0, -1, 9), (0, 0, 0), 440, 14, (.56, .78, 1))
    sky_light.data.specular_factor = .15
    sun_light('Very low red sunlight', (.14, -.95, -.055), .65, (1, .37, .12), .045)
    scene['refinement'] = 'Low shore-level perspective, a small thorn and cord in the sand, footprints, irregular foam, crossed water ripples and reflected sunset.'


def configure(scene_name, preview):
    scene = bpy.context.scene
    scene.render.engine = 'CYCLES'
    scene.cycles.samples = 28 if preview else 96
    scene.cycles.use_denoising = True
    scene.cycles.adaptive_threshold = .025 if preview else .012
    scene.cycles.max_bounces = 6
    scene.cycles.transparent_max_bounces = 5
    scene.render.threads_mode = 'FIXED'
    scene.render.threads = 8
    scene.render.resolution_x = 720 if preview else 1440
    scene.render.resolution_y = 660 if preview else 1320
    if scene_name == 'serpent':
        scene.render.resolution_x = 600 if preview else 1200
        scene.render.resolution_y = 1100 if preview else 2200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = 'PNG'
    scene.render.image_settings.color_mode = 'RGB'
    if scene_name != 'serpent':
        scene.view_settings.view_transform = 'AgX'
        scene.view_settings.look = 'AgX - Medium High Contrast'
    scene.render.filepath = str((BUILD if preview else ASSETS) / (scene_name + '.png'))
    scene.render.use_file_extension = True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--scene', choices=['matachin', 'serpent', 'shore', 'combray', 'casa', 'all'], required=True)
    parser.add_argument('--preview', action='store_true')
    parser.add_argument('--final', action='store_true')
    args = parser.parse_args(sys.argv[sys.argv.index('--') + 1:])
    names = ['matachin', 'serpent', 'shore', 'combray', 'casa'] if args.scene == 'all' else [args.scene]
    for name in names:
        base = ROOT / 'build' / ('serpent-study.blend' if name == 'serpent' else name + '-panel.blend')
        if not base.exists():
            base = ROOT / 'build' / ('serpent-study.blend' if name == 'serpent' else name + '.blend')
        if not base.exists():
            original_argv = sys.argv[:]
            script = 'serpent_study.py' if name == 'serpent' else 'urth_scenes.py'
            sys.argv = ['blender', '--', '--build-only']
            if name != 'serpent':
                sys.argv.extend(['--scene', name])
            runpy.run_path(str(ROOT / 'art' / script), run_name='__main__')
            sys.argv = original_argv
        bpy.ops.wm.open_mainfile(filepath=str(base))
        rng.seed(9193)
        globals()[name]()
        configure(name, args.preview)
        bpy.ops.wm.save_as_mainfile(filepath=str(BUILD / (name + '.blend')), compress=True)
        bpy.ops.render.render(write_still=True)


if __name__ == '__main__':
    main()
