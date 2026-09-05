"""Blender sculpture study after Sam Weber's Book of the New Sun binding.

The supplied cover is the compositional reference. The head, serpent, drops,
and plaque are 3D geometry; only the small heraldic panel uses a texture crop.
Source art: https://www.foliosociety.com/usa/the-book-of-the-new-sun-2-volume

blender -b --factory-startup --python art/serpent_study.py -- --preview
blender -b --factory-startup --python art/serpent_study.py -- --final --banner
"""
import argparse
import math
import sys
from pathlib import Path
from array import array
import json

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT=Path(__file__).resolve().parents[1]
BUILD=ROOT/"build"
ASSETS=ROOT/"assets"
BUILD.mkdir(exist_ok=True)
ASSETS.mkdir(exist_ok=True)
p=argparse.ArgumentParser()
p.add_argument("--preview",action="store_true")
p.add_argument("--final",action="store_true")
p.add_argument("--banner",action="store_true")
p.add_argument("--reference",type=Path,default=Path(__file__).parent/"cover-reference.png")
args=p.parse_args(sys.argv[sys.argv.index("--")+1:] if "--" in sys.argv else [])
bpy.ops.object.select_all(action="SELECT")
bpy.ops.object.delete(use_global=False)
scene=bpy.context.scene
scene.render.engine="CYCLES"
scene.cycles.device="CPU"
scene.cycles.samples=32 if args.preview else 80
scene.cycles.use_denoising=True
scene.cycles.max_bounces=5
scene.render.threads_mode="FIXED"
scene.render.threads=8
scene.render.resolution_x=1800 if args.banner else 1200
scene.render.resolution_y=1100 if args.banner else 1600
scene.render.resolution_percentage=65 if args.preview else 100
scene.render.image_settings.file_format="PNG"
scene.render.image_settings.color_mode="RGB"
scene.world.use_nodes=True
scene.world.node_tree.nodes["Background"].inputs[0].default_value=(.55,.65,.8,1)
scene.world.node_tree.nodes["Background"].inputs[1].default_value=.30
scene.view_settings.view_transform="Standard"
scene.view_settings.look="None"
scene.view_settings.exposure=0

def linear(c):
    return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4
def rgb(hexvalue):
    h=hexvalue.lstrip('#')
    return tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))

def material(name,color,rough=.72,metal=0,emit=0,grain=0):
    m=bpy.data.materials.new(name)
    m.diffuse_color=(*rgb(color),1)
    m.use_nodes=True
    nodes=m.node_tree.nodes
    bs=nodes.get("Principled BSDF")
    bs.inputs["Base Color"].default_value=(*rgb(color),1)
    bs.inputs["Roughness"].default_value=rough
    bs.inputs["Metallic"].default_value=metal
    if emit:
        bs.inputs["Emission Color"].default_value=(*rgb(color),1)
        bs.inputs["Emission Strength"].default_value=emit
    if grain:
        noise=nodes.new("ShaderNodeTexNoise")
        noise.inputs["Scale"].default_value=75
        noise.inputs["Detail"].default_value=2
        bump=nodes.new("ShaderNodeBump")
        bump.inputs["Strength"].default_value=grain
        bump.inputs["Distance"].default_value=.015
        m.node_tree.links.new(noise.outputs["Fac"],bump.inputs["Height"])
        m.node_tree.links.new(bump.outputs["Normal"],bs.inputs["Normal"])
    return m

blue=material("Ultramarine / carved stone","1D3270",.75,grain=.12)
dark_blue=material("Blue-black recesses","111A38",.87)
blue_edge=material("Cut planes / blue","1E2C5C",.8)
red=material("Vermilion","E53620",.68,grain=.10)
gold=material("Yellow wax","FFE11B",.40,emit=.08)
plate_red=material("Red enamel plaque","E82E19",.50)
field=material("Flat yellow field","FFDC20",.86,emit=.7)

def mesh(name,verts,faces,mat,smooth=True):
    d=bpy.data.meshes.new(name)
    d.from_pydata(verts,[],faces)
    d.update()
    o=bpy.data.objects.new(name,d)
    scene.collection.objects.link(o)
    d.materials.append(mat)
    if smooth:
        for poly in d.polygons:
            poly.use_smooth=True
    return o

def sphere(name,pos,scale,mat):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=64,ring_count=40,radius=1,location=pos)
    o=bpy.context.object
    o.name=name
    o.scale=scale
    o.data.materials.append(mat)
    for f in o.data.polygons:
        f.use_smooth=True
    return o

def cube(name,pos,dims,mat,bevel=.03):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    o=bpy.context.object
    o.name=name
    o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    o.data.materials.append(mat)
    if bevel:
        mod=o.modifiers.new("Soft edge","BEVEL")
        mod.width=bevel
        mod.segments=3
        o.modifiers.new("Weighted normals","WEIGHTED_NORMAL")
    return o

def curve(name,points,radius,mat):
    d=bpy.data.curves.new(name,"CURVE")
    d.dimensions="3D"
    d.bevel_depth=radius
    d.bevel_resolution=3
    s=d.splines.new("POLY")
    s.points.add(len(points)-1)
    for p,co in zip(s.points,points):
        p.co=(*co,1)
    o=bpy.data.objects.new(name,d)
    scene.collection.objects.link(o)
    d.materials.append(mat)
    return o

# An openly licensed anatomical base, recast as an ultramarine sculpture.
# Infinite 3D head scan: Lee Perry-Smith / I-R Entertainment Ltd., CC BY 3.0.
# The source is retained in art/LeePerrySmith.glb and credited in the scene notes.
for ob in list(scene.objects):
    bpy.data.objects.remove(ob,do_unlink=True)
bpy.ops.import_scene.gltf(filepath=str(Path(__file__).parent/'LeePerrySmith.glb'))
anatomy=bpy.data.objects.get('LeePerrySmith')
for ob in list(scene.objects):
    if ob!=anatomy:
        bpy.data.objects.remove(ob,do_unlink=True)
anatomy.name='Blue bust / adapted Lee Perry-Smith anatomical base'
anatomy.scale=(.64,.57,.65)
anatomy.location=(.045,.40,.48)
bpy.context.view_layer.objects.active=anatomy
anatomy.select_set(True)
bpy.ops.object.transform_apply(location=True,rotation=True,scale=True)
anatomy.data.materials.clear()
anatomy.data.materials.append(blue)
for f in anatomy.data.polygons:
    f.use_smooth=True
sub=anatomy.modifiers.new('Smooth anatomical planes','SUBSURF')
sub.levels=2
sub.render_levels=2
bpy.ops.object.modifier_apply(modifier=sub.name)
bpy.context.view_layer.update()
anatomy_bvh=BVHTree.FromObject(anatomy,bpy.context.evaluated_depsgraph_get())
def front_y(x,z):
    hit=anatomy_bvh.ray_cast(Vector((x,-8,z)),Vector((0,1,0)),20)
    return hit[0].y if hit[0] is not None else -.3

def catmull(points,steps=14):
    p=[Vector(points[0])]+[Vector(v) for v in points]+[Vector(points[-1])]
    out=[]
    for i in range(1,len(p)-2):
        a,b,c,d=p[i-1:i+3]
        for k in range(steps):
            t=k/steps
            out.append(.5*((2*b)+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
    out.append(Vector(points[-1]))
    return out

# One continuous serpent winds over the brow, crown, cheek, and throat.
control=[(1.00,.37,2.44),(1.16,-.20,2.78),(.82,-.76,2.97),(.26,-1.00,2.59),(-.31,-1.03,2.38),(-.91,-.91,2.20),(-1.26,-.49,1.99),(-1.15,.35,2.37),(-.87,.42,3.08),(-.34,.08,3.47),(.20,-.29,3.48),(.64,-.68,3.23),(.84,-.94,2.80),(.81,-1.06,2.23),(.73,-1.09,1.66),(1.16,-.27,1.30),(1.17,.55,1.04),(.06,1.04,.80),(-1.06,.37,.62),(-1.06,-.48,.16),(-.85,-.93,-.37),(-.27,-.80,-.81),(.54,.38,-.98),(.99,-.14,-1.14),(.98,-.69,-1.47),(.61,-.97,-1.69),(.22,-1.02,-1.65)]
path=catmull(control,16)
fitted=[]
for vtx in path:
    q=vtx.copy()
    q.z-=.34*max(0,min(1,(q.z-2.7)/.5))
    nearest=anatomy_bvh.find_nearest(q)
    if nearest[0] is not None:
        q=nearest[0]+nearest[1]*.174
    fitted.append(q)
path=[fitted[0]]+[(fitted[i-1]+2*fitted[i]+fitted[i+1])/4 for i in range(1,len(fitted)-1)]+[fitted[-1]]
snake_head_offset=path[-1]-Vector(control[-1])
snake=bpy.data.materials.new("Serpent / red engraved diamond scales")
snake.use_nodes=True
nodes=snake.node_tree.nodes
links=snake.node_tree.links
bs=nodes.get("Principled BSDF")
bs.inputs["Roughness"].default_value=.64
uv=nodes.new("ShaderNodeTexCoord")
sep=nodes.new("ShaderNodeSeparateXYZ")
links.new(uv.outputs["UV"],sep.inputs[0])

def math_node(op,a,b=None):
    n=nodes.new("ShaderNodeMath")
    n.operation=op
    if isinstance(a,(float,int)):
        n.inputs[0].default_value=a
    else: links.new(a,n.inputs[0])
    if b is not None:
        if isinstance(b,(float,int)): n.inputs[1].default_value=b
        else: links.new(b,n.inputs[1])
    return n.outputs[0]

u=math_node("MULTIPLY",sep.outputs['X'],20.0)
v=math_node("MULTIPLY",sep.outputs['Y'],10.0)
diag1=math_node("PINGPONG",math_node("ADD",u,v),1.0)
diag2=math_node("PINGPONG",math_node("SUBTRACT",u,v),1.0)
line1=math_node("LESS_THAN",diag1,.16)
line2=math_node("LESS_THAN",diag2,.16)
mask=math_node("MAXIMUM",line1,line2)
mix=nodes.new("ShaderNodeMixRGB")
mix.blend_type="MIX"
links.new(mask,mix.inputs[0])
mix.inputs[1].default_value=(*rgb("172F6B"),1)
mix.inputs[2].default_value=(*rgb("F23C24"),1)
links.new(mix.outputs[0],bs.inputs['Base Color'])
bump=nodes.new("ShaderNodeBump")
bump.inputs['Strength'].default_value=.23
bump.inputs['Distance'].default_value=.019
links.new(mask,bump.inputs['Height'])
links.new(bump.outputs[0],bs.inputs['Normal'])

sv=[];sf=[];uvvalues=[]
arclength=[0]
for a,b in zip(path,path[1:]):
    arclength.append(arclength[-1]+(b-a).length)
section=32
last_normal=None
for i,pnt in enumerate(path):
    tangent=(path[min(i+1,len(path)-1)]-path[max(i-1,0)]).normalized()
    if last_normal is None:
        normal=tangent.cross(Vector((0,0,1)))
        if normal.length<.01: normal=tangent.cross(Vector((0,1,0)))
        normal.normalize()
    else:
        normal=last_normal-tangent*last_normal.dot(tangent)
        normal.normalize()
    binormal=tangent.cross(normal).normalized()
    last_normal=normal
    t=i/(len(path)-1)
    radius=.145*min(1,.18+t*23)
    for j in range(section):
        a=math.tau*j/section
        sv.append(pnt+radius*(math.cos(a)*normal+math.sin(a)*binormal))
    if i:
        for j in range(section):
            sf.append(((i-1)*section+j,(i-1)*section+(j+1)%section,i*section+(j+1)%section,i*section+j))
            uvvalues.extend([(arclength[i-1],j/section),(arclength[i-1],(j+1)/section),(arclength[i],(j+1)/section),(arclength[i],j/section)])
snake_obj=mesh("Serpent / continuous coiled body",sv,sf,snake)
uv_layer=snake_obj.data.uv_layers.new(name="Scales")
for loop,val in zip(uv_layer.data,uvvalues):
    loop.uv=val

# The head of the snake rests at the collar. Its jaw and eyes are modeled.
snake_head=sphere("Serpent / head",(.11,-1.045,-1.64),(.255,.18,.135),red)
snake_head.rotation_euler[1]=-.13
for side in (-1,1):
    sphere("Serpent / eye",(.045,-1.045+side*.166,-1.57),(.019,.011,.013),gold)
    sphere("Serpent / pupil",(.038,-1.045+side*.178,-1.57),(.006,.007,.013),dark_blue)
curve("Serpent / closed mouth",[(-.13,-1.126,-1.68),(-.045,-1.215,-1.70),(.14,-1.201,-1.71),(.28,-1.14,-1.69)],.008,dark_blue)
for k in range(4):
    x=-.03+k*.07
    curve("Serpent / head scale",[(x-.045,-1.137,-1.53),(x,-1.197,-1.545),(x+.04,-1.14,-1.57)],.008,dark_blue)
for ob in scene.objects:
    if ob.name.startswith(('Serpent / head','Serpent / eye','Serpent / pupil','Serpent / closed mouth')):
        ob.location+=snake_head_offset

def drop(name,x,y,z,length,width):
    # A pointed wax drop, flattened slightly into the face.
    profile=[(0,0),(.035,.48),(.09,.83),(.19,1),(.33,.82),(.52,.48),(.78,.18),(1,0)]
    vv=[];ff=[];segments=32
    for h,r in profile:
        for j in range(segments):
            a=math.tau*j/segments
            vv.append((x+width*r*math.cos(a),y+width*.6*r*math.sin(a),z+h*length))
    for i in range(len(profile)-1):
        for j in range(segments):
            ff.append((i*segments+j,i*segments+(j+1)%segments,(i+1)*segments+(j+1)%segments,(i+1)*segments+j))
    return mesh(name,vv,ff,gold)

for x,z,l,w in [(-.43,2.87,.16,.026),(.15,3.04,.11,.020),(-.31,2.59,.32,.020),(.28,2.02,.25,.036),(.44,2.11,.14,.026),(-.91,1.29,.17,.027),(.92,.96,.15,.023),(.78,.33,.29,.040),(-.61,.37,.23,.037),(-.48,-.02,.17,.031),(.44,-.43,.13,.026)]:
    y=front_y(x,z+l*.3)-.025
    drop("Yellow drop / face",x,y,z,l,w)
drop("Yellow drop / throat",.02,front_y(.02,-.48)-.02,-.60,.24,.039)
drop("Yellow drop / shoulder",-1.36,front_y(-1.36,-1.20)-.02,-1.30,.25,.038)
drop("Yellow drop / cloak",1.60,front_y(1.60,-1.16)-.02,-1.25,.22,.033)
drop("Yellow drop / chest",-.42,front_y(-.42,-1.80)-.02,-1.85,.10,.028)

# Red enamel plate with a fine yellow lip, centered across the face.
cube("Heraldic plaque / enamel",(0,-1.42,1.05),(1.30,.080,1.30),plate_red,.009)
for x in (-.642,.642):
    cube("Plaque / yellow border",(x,-1.467,1.05),(.017,.013,1.285),gold,.002)
for z in (.410,1.690):
    cube("Plaque / yellow border",(0,-1.467,z),(1.29,.013,.017),gold,.002)

# The user-supplied panel is retained as a decal, with source attribution.
if args.reference.exists():
    ref=bpy.data.images.load(str(args.reference))
    W,H=ref.size
    pixels=array('f',[0])*(W*H*4)
    ref.pixels.foreach_get(pixels)
    x0,y0,x1,y1=211,252,321,362
    crop_w,crop_h=x1-x0,y1-y0
    crop=array('f')
    for yy in range(H-y1,H-y0):
        crop.extend(pixels[(yy*W+x0)*4:(yy*W+x1)*4])
    emblem=bpy.data.images.new("Cover panel / Sam Weber reference",width=crop_w,height=crop_h,alpha=True)
    emblem.pixels.foreach_set(crop)
    emblem.pack()
    decal_mat=bpy.data.materials.new("Heraldic panel / source artwork decal")
    decal_mat.use_nodes=True
    n=decal_mat.node_tree.nodes
    tex=n.new("ShaderNodeTexImage")
    tex.image=emblem
    bs=n.get("Principled BSDF")
    decal_mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Base Color'])
    decal_mat.node_tree.links.new(tex.outputs['Color'],bs.inputs['Emission Color'])
    bs.inputs['Emission Strength'].default_value=.25
    bs.inputs['Roughness'].default_value=.65
    decal=mesh("Heraldic panel / face",[(-.628,-1.472,.422),(.628,-1.472,.422),(.628,-1.472,1.678),(-.628,-1.472,1.678)],[(0,1,2,3)],decal_mat,False)
    uv=decal.data.uv_layers.new(name="Panel")
    for loop,value in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):loop.uv=value

# Resize the plaque against the anatomical face.
for ob in scene.objects:
    if ob.name.startswith(('Heraldic plaque','Plaque /','Heraldic panel / face')):
        ob.location.x*=.80
        ob.location.z=1.13+(ob.location.z-1.05)*.80
        ob.scale.x*=.80
        ob.scale.z*=.80
        ob.location.y-=.025

# The field is flat pigment for the camera, with neutral illumination on the bust.
wn=scene.world.node_tree.nodes
wl=scene.world.node_tree.links
camera_bg=wn.new('ShaderNodeBackground')
camera_bg.inputs[0].default_value=(*rgb('FFDD19'),1)
camera_bg.inputs[1].default_value=1
lp=wn.new('ShaderNodeLightPath')
mix_world=wn.new('ShaderNodeMixShader')
wl.new(lp.outputs['Is Camera Ray'],mix_world.inputs[0])
wl.new(wn.get('Background').outputs[0],mix_world.inputs[1])
wl.new(camera_bg.outputs[0],mix_world.inputs[2])
wl.new(mix_world.outputs[0],wn.get('World Output').inputs[0])
bpy.ops.object.camera_add(location=(2.15,-16.0,1.0))
cam=bpy.context.object
cam.name="Cover study camera"
cam.rotation_euler=(Vector((0,0,.62))-cam.location).to_track_quat('-Z','Y').to_euler()
cam.data.type="ORTHO"
cam.data.sensor_fit='HORIZONTAL'
cam.data.ortho_scale=10.3 if args.banner else 4.7
scene.camera=cam

def area(name,pos,power,size,color):
    d=bpy.data.lights.new(name,'AREA')
    d.energy=power
    d.shape='DISK'
    d.size=size
    d.color=color
    o=bpy.data.objects.new(name,d)
    scene.collection.objects.link(o)
    o.location=pos
    o.rotation_euler=(Vector((0,0,.6))-o.location).to_track_quat('-Z','Y').to_euler()
area("Large side light",(-4,-6,7),650,5,(.85,.91,1))
area("Blue form / soft fill",(5,-3,2),170,4,(.75,.85,1))
area("Crown edge",(1,1,6),450,3,(.70,.80,1))

scene['reference_artist']='Sam Weber'
scene['reference_work']='Bindings for The Book of the New Sun, The Folio Society'
scene['reference_url']='https://www.foliosociety.com/usa/the-book-of-the-new-sun-2-volume'
scene['study_note']='Sculptural interpretation. Only the small heraldic decal is cropped from the user-supplied reference.'
scene['head_model_credit']='Infinite head scan: Lee Perry-Smith / I-R Entertainment Ltd. CC BY 3.0. Converted for three.js.'
scene['head_model_source']='https://threejs.org/examples/models/gltf/LeePerrySmith/LeePerrySmith.glb'
suffix='banner' if args.banner else 'portrait'
scene.render.filepath=str(BUILD/f"serpent-{suffix}-preview.png" if args.preview else ASSETS/f"serpent-{suffix}.png")
bpy.ops.wm.save_as_mainfile(filepath=str(BUILD/"serpent-study.blend"),compress=True)
bpy.ops.render.render(write_still=True)
