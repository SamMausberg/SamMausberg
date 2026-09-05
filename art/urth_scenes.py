"""Two Blender studies for a Book of the New Sun profile triptych.

Matachin: the metal tower, with its former propulsion chamber below ground.
Shore: a symbolic composition responding to the passage supplied by the user.
The architecture and object arrangements are interpretations, not canonical maps.

blender -b --factory-startup --python art/urth_scenes.py -- --scene matachin --preview
blender -b --factory-startup --python art/urth_scenes.py -- --scene shore --final
"""
import argparse
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Vector

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / 'build'
ASSETS = ROOT / 'assets'
BUILD.mkdir(exist_ok=True)
ASSETS.mkdir(exist_ok=True)
p = argparse.ArgumentParser()
p.add_argument('--scene', choices=['matachin', 'shore', 'combray', 'casa'], required=True)
p.add_argument('--preview', action='store_true')
p.add_argument('--final', action='store_true')
args = p.parse_args(sys.argv[sys.argv.index('--')+1:])
rng = random.Random(1931)
bpy.ops.object.select_all(action='SELECT')
bpy.ops.object.delete(use_global=False)
s = bpy.context.scene
s.render.engine = 'CYCLES'
s.cycles.samples = 28 if args.preview else 88
s.cycles.use_denoising = True
s.cycles.max_bounces = 5
s.render.threads_mode = 'FIXED'
s.render.threads = 6
s.render.resolution_x = 1200
s.render.resolution_y = 1600
s.render.resolution_percentage = 50 if args.preview else 100
s.render.image_settings.file_format = 'PNG'
s.render.image_settings.color_mode = 'RGB'
s.view_settings.view_transform = 'AgX'
s.view_settings.look = 'AgX - Medium High Contrast'
s.world.use_nodes = True
s.world.node_tree.nodes['Background'].inputs[0].default_value = (.26,.33,.44,1)
s.world.node_tree.nodes['Background'].inputs[1].default_value = .28

def material(name, color, rough=.7, metal=0, grain=0, glow=0):
    m = bpy.data.materials.new(name)
    m.diffuse_color = (*color,1)
    m.use_nodes = True
    n=m.node_tree.nodes
    b=n.get('Principled BSDF')
    b.inputs['Base Color'].default_value=(*color,1)
    b.inputs['Roughness'].default_value=rough
    b.inputs['Metallic'].default_value=metal
    if glow:
        b.inputs['Emission Color'].default_value=(*color,1)
        b.inputs['Emission Strength'].default_value=glow
    if grain:
        noise=n.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value=52
        noise.inputs['Detail'].default_value=3
        bump=n.new('ShaderNodeBump')
        bump.inputs['Strength'].default_value=grain
        bump.inputs['Distance'].default_value=.05
        m.node_tree.links.new(noise.outputs['Fac'],bump.inputs['Height'])
        m.node_tree.links.new(bump.outputs[0],b.inputs['Normal'])
    return m

def paint(o,m):
    o.data.materials.append(m)
    return o

def mesh(name,verts,faces,m,smooth=False):
    d=bpy.data.meshes.new(name)
    d.from_pydata(verts,[],faces)
    d.update()
    o=bpy.data.objects.new(name,d)
    s.collection.objects.link(o)
    paint(o,m)
    if smooth:
        for f in d.polygons: f.use_smooth=True
    return o

def cube(name,pos,dims,m,bevel=.03,rotation=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=pos)
    o=bpy.context.object
    o.name=name
    o.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    if rotation: o.rotation_euler=rotation
    if bevel:
        b=o.modifiers.new('Worn edges','BEVEL')
        b.width=bevel
        b.segments=2
        o.modifiers.new('Weighted normals','WEIGHTED_NORMAL')
    return paint(o,m)

def cyl(name,pos,r,depth,m,top=None,vertices=80):
    if top is None:
        bpy.ops.mesh.primitive_cylinder_add(vertices=vertices,radius=r,depth=depth,location=pos)
    else:
        bpy.ops.mesh.primitive_cone_add(vertices=vertices,radius1=r,radius2=top,depth=depth,location=pos)
    o=bpy.context.object
    o.name=name
    for f in o.data.polygons: f.use_smooth=True
    return paint(o,m)

def sphere(name,pos,scale,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=32,ring_count=20,radius=1,location=pos)
    o=bpy.context.object
    o.name=name
    o.scale=scale
    for f in o.data.polygons: f.use_smooth=True
    return paint(o,m)

def tube(name,points,r,m,closed=False):
    d=bpy.data.curves.new(name,'CURVE')
    d.dimensions='3D'
    d.bevel_depth=r
    d.bevel_resolution=2
    sp=d.splines.new('POLY')
    sp.points.add(len(points)-1)
    for a,b in zip(sp.points,points): a.co=(*b,1)
    sp.use_cyclic_u=closed
    o=bpy.data.objects.new(name,d)
    s.collection.objects.link(o)
    return paint(o,m)

def camera(pos,target,scale):
    bpy.ops.object.camera_add(location=pos)
    c=bpy.context.object
    c.name='Portrait composition'
    c.rotation_euler=(Vector(target)-c.location).to_track_quat('-Z','Y').to_euler()
    c.data.type='ORTHO'
    c.data.sensor_fit='HORIZONTAL'
    c.data.ortho_scale=scale
    s.camera=c
    return c

def area(name,pos,target,power,size,color):
    d=bpy.data.lights.new(name,'AREA')
    d.energy=power
    d.shape='DISK'
    d.size=size
    d.color=color
    o=bpy.data.objects.new(name,d)
    s.collection.objects.link(o)
    o.location=pos
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def arch(name,cx,y,z,width,height,depth,m):
    # Voussoirs form an open arch. There is no fake black decal over a wall.
    rad=width/2
    base=z+height-rad
    for x in (cx-rad-.15,cx+rad+.15):
        cube(name+' / pier',(x,y,z+(height-rad)/2),(.30,depth,height-rad),m,.035)
    for i in range(13):
        a=math.pi*i/13+.014
        b=math.pi*(i+1)/13-.014
        outline=[(cx+rad*math.cos(a),base+rad*math.sin(a)),(cx+(rad+.30)*math.cos(a),base+(rad+.30)*math.sin(a)),(cx+(rad+.30)*math.cos(b),base+(rad+.30)*math.sin(b)),(cx+rad*math.cos(b),base+rad*math.sin(b))]
        vv=[(xx,yy,zz) for yy in (y-depth/2,y+depth/2) for xx,zz in outline]
        mesh(name+' / arch stone',vv,[(0,3,2,1),(4,5,6,7),(0,1,5,4),(1,2,6,5),(2,3,7,6),(3,0,4,7)],m)

def lathe(name,profile,m,center=(0,0),segments=128):
    vv=[];ff=[]
    for z,r in profile:
        for j in range(segments):
            a=math.tau*j/segments
            vv.append((center[0]+r*math.cos(a),center[1]+r*math.sin(a),z))
    for k in range(len(profile)-1):
        for j in range(segments):
            ff.append((k*segments+j,k*segments+(j+1)%segments,(k+1)*segments+(j+1)%segments,(k+1)*segments+j))
    return mesh(name,vv,ff,m,True)

if args.scene=='matachin':
    teal=material('Ancient hull / verdigris',(.026,.10,.115),.65,.62,.50)
    oxide=material('Patina seams',(.055,.16,.15),.82,.4,.45)
    copper=material('Exposed worn bronze',(.29,.105,.041),.57,.65,.2)
    basalt=material('Basalt and old mortar',(.048,.065,.082),.89,grain=.5)
    stones=[material('Sandstone '+str(i),(.19+i*.018,.18+i*.015,.125+i*.015),grain=.40) for i in range(4)]
    dark=material('Unlit interior',(.004,.009,.012),.96)
    orange=material('Warm rooms',(.80,.20,.03),.7,glow=2)
    red=material('The old sun',(.68,.07,.019),.98,glow=.5)
    sand=material('Dust in the courtyard',(.17,.16,.12),.94,grain=.65)
    bg=material('Far dusk',(.047,.073,.09),.9,glow=.3)
    cube('Courtyard ground',(0,1,-.16),(80,80,.3),sand,0)
    # Tall, smooth-sided metal silhouette. Its external design is an interpretation.
    lathe('Matachin / former vessel',[(.1,1.36),(1,1.37),(3,1.36),(10.5,1.3),(12.7,1.27),(13.5,1.19),(14.2,.86),(14.7,.32),(14.85,0)],teal,center=(0,1.5))
    for k in range(18):
        a=math.tau*k/18
        tube('Longitudinal plating',[(1.375*math.cos(a),1.5+1.375*math.sin(a),.5),(1.29*math.cos(a),1.5+1.29*math.sin(a),12.6),(1.20*math.cos(a),1.5+1.20*math.sin(a),13.4),(.84*math.cos(a),1.5+.84*math.sin(a),14.2)],.019,oxide)
    for z in [.65,1.2,2.4,4.0,5.6,7.2,8.8,10.4,12,12.8,13.5]:
        r=1.395-.009*z
        tube('Hull circumference',[(r*math.cos(a),1.5+r*math.sin(a),z) for a in [math.tau*i/128 for i in range(128)]],.035,copper if z in (1.2,12.8) else oxide,True)
    for z in [3.3,4.9,6.5,8.1,9.7,11.3]:
        for k in range(12):
            a=math.tau*k/12+.08
            r=1.381-.006*z
            cube('Narrow openings',(r*math.cos(a),1.5+r*math.sin(a),z),(.18,.035,.62),orange if (k+int(z))%17==0 else dark,.07,(0,0,a+math.pi/2))
            cube('Metal sill',(r*math.cos(a),1.5+r*math.sin(a),z-.34),(.24,.12,.04),copper,.008,(0,0,a+math.pi/2))
    # Exterior conduits disappear below grade; the propulsion chamber is underground.
    for k in range(5):
        a=-1.65+k*.15
        x,y=1.41*math.cos(a),1.5+1.41*math.sin(a)
        tube('Old conduits disappearing beneath the tower',[(x*1.5,y-.4,-.5),(x*1.5,y-.4,.3),(x,y,.9),(x,y,2.8+k*.37)],.07,copper)
        for z in [1.0,1.5,2,2.5]: sphere('Conduit clips',(x,y,z),(.085,.085,.065),oxide)
    # Inhabited masonry has accumulated around the hull, leaving it legible.
    for side in (-1,1):
        for j in range(8):
            z=.2+j*.35
            for k in range(5):
                x=side*(1.47+k*.32)
                cube('Later foundation stone',(x,1.32,z),(.30,.72,.32),rng.choice(stones),.028)
        cube('Guild wing',(side*3.10,2.2,2.5),(2.5,3.0,5.0),basalt,.04)
        for level in range(5):
            for col in range(3):
                x=side*3.10+(col-1)*.63
                cube('Annex ashlar',(x,.68,.4+level*.78),(.58,.15,.67),rng.choice(stones),.035)
        arch('Lower arcade',side*3.05,.35,.05,1.0,2.2,.55,stones[1])
        for z in (3.2,4.2):
            for x in (side*3.1-.65,side*3.1,side*3.1+.65):
                cube('Occupied annex window',(x,.665,z),(.23,.03,.53),dark,.06)
        cyl('Wing roof',(side*3.1,2.2,5.15),1.7,.25,copper,top=1.3,vertices=4).rotation_euler[2]=math.pi/4
    # A central entrance and a stair approach at ground level.
    arch('Masters entrance',0,.03,.0,.84,1.95,.42,stones[2])
    cube('Entrance shadow',(0,.06,.79),(.83,.12,1.55),dark,.02)
    for i in range(11):
        cube('Approach treads',(0,-3.9+i*.33,-.1+i*.023),(1.66,.38,.09),stones[2],.025)
    # Distant metal towers are old vessels too; no generic turret crowns.
    for x,y,h,r in [(-4.9,7,11.0,.67),(4.0,8,12.5,.76),(-2.8,12,15,.43),(6.0,15,10.2,.65)]:
        lathe('Distant metal spire',[(0,r),(h-.8,r),(h-.3,r*.65),(h,0)],oxide,center=(x,y),segments=64)
        for z in range(2,int(h),2): cyl('Distant collar',(x,y,z),r*1.05,.07,copper,vertices=64)
    for side in (-1,1):
        for j in range(7):
            arch('Aged passage',side*(4.5+j*1.3),-1.1,.0,.86,3.5,.6,stones[j%4])
    # An isolated human figure supplies scale without assigning an episode or sword.
    cloak=material('A passerby',(.006,.012,.015),.98)
    cyl('Cloaked figure',(.67,-3.1,.41),.18,.70,cloak,top=.08,vertices=24)
    sphere('Head',(.67,-3.1,.86),(.105,.105,.12),cloak)
    for k in range(90):
        x,y=rng.uniform(-8,8),rng.uniform(-7,6)
        if abs(x)<1: continue
        sphere('Courtyard rubble',(x,y,.035),(rng.uniform(.025,.09),rng.uniform(.03,.12),rng.uniform(.02,.07)),rng.choice(stones))
    cam=camera((17,-34,15.5),(0,1,7.1),13.2)
    # A muted red sun behind the tower gives a clear, spare silhouette.
    sun=cyl('Red sun disc',(-7,25,9.6),3.0,.035,red,vertices=160)
    sun.rotation_euler=cam.rotation_euler
    cube('Backdrop',(0,50,15),(100,.1,100),bg,0)
    area('Cool sky',(-9,-10,22),(0,2,7),2000,10,(.6,.77,1))
    area('Last red light',(0,10,19),(0,1,8),2900,7,(1,.45,.20))
    area('Courtyard bounce',(4,-8,8),(0,1,4),850,8,(1,.79,.50))
    s['literary_basis']='The Shadow of the Torturer, chapter III: metal tower; former propulsion chamber underground; oubliette beneath and outside tower.'
    s['interpretation']='The hull silhouette, annexes, window arrangement, conduits, and courtyard composition are invented.'

elif args.scene=='shore':
    sand=material('Sacred sand',(.37,.245,.105),.91,grain=.70)
    wet=material('Wet sand',(.16,.136,.068),.34,grain=.55)
    water=material('Evening sea',(.012,.095,.105),.22,.38,grain=.04)
    foam=material('Lace of foam',(.48,.57,.43),.79,grain=.4)
    black=material('Curved thorn',(.011,.018,.021),.46,grain=.7)
    cord=material('Worn cord',(.29,.17,.055),.93,grain=.4)
    leather=material('Travelled leather',(.041,.036,.025),.78,grain=.6)
    sole=material('Worn soles',(.017,.026,.024),.96)
    stitch=material('Boot seams',(.17,.139,.067),.9)
    pebble=material('Sea-worn stones',(.11,.15,.145),.62,grain=.4)
    sky=material('Sea haze',(.052,.128,.143),.98,glow=.7)
    red=material('Distant old sun',(.75,.13,.029),.9,glow=.6)
    cube('Beach',(0,0,-.20),(100,100,.3),sand,0)
    # Broad shoreline with small crossing ripples, all actual geometry.
    vv=[];ff=[]
    nx,ny=160,170
    for j in range(ny+1):
        y=-.2+j*40/ny
        for i in range(nx+1):
            x=-30+i*60/nx
            shore=-.1+.4*math.sin(.28*x)+.15*math.sin(.79*x)
            yy=y+shore
            z=.005+.012*math.sin(x*1.3+y*8)+.027*math.sin(y*3.9+x*.35)+.006*math.sin(12*x+11*y)
            z*=min(1,max(0,y/.6))
            vv.append((x,yy,z))
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i
            ff.append((a,a+1,a+nx+2,a+nx+1))
    mesh('Surface of the sea',vv,ff,water,True)
    # Wet sand at the edge follows the same irregular contour.
    vv=[]
    for row in (0,1):
        for i in range(161):
            x=-30+60*i/160
            y=-.1+.4*math.sin(.28*x)+.15*math.sin(.79*x)-row*1.15
            vv.append((x,y,-.034))
    mesh('A dark band left by a wave',vv,[(i,i+1,i+162,i+161) for i in range(160)],wet)
    for j in range(8):
        base=.1+j*.55+j*j*.06
        points=[]
        for i in range(360):
            x=-25+50*i/359
            y=base+.4*math.sin(.28*x)+.15*math.sin(.79*x)+.05*math.sin(x*4+j)
            z=.045+.006*math.sin(x*1.1)
            points.append((x,y,z))
        if j==0:
            tube('Thin breaking wave',points,.021,foam)
        else:
            for start in range((j%3)*13,320,47):
                tube('Broken foam line',points[start:start+31+j%4],.008,foam)
    for k in range(650):
        x=rng.uniform(-20,20)
        y=.1+.4*math.sin(.28*x)+.15*math.sin(.79*x)+rng.expovariate(4)
        sphere('Foam fleck',(x,y,.047),(rng.uniform(.006,.026),rng.uniform(.02,.10),.003),foam)
    for k in range(280):
        x,y=rng.uniform(-13,13),rng.uniform(-12,-1.7)
        size=rng.uniform(.007,.04)
        sphere('Sand and pebbles',(x,y,-.018),(size,size*rng.uniform(.6,1.8),size*.35),pebble if k%4==0 else sand)
    # The thorn is enlarged as a symbolic foreground object, not a jeweled talisman.
    control=[(-1.5,-5.1,.02,.30),(-1.34,-5.15,.52,.29),(-1.06,-5.2,1.08,.23),(-.63,-5.20,1.63,.18),(-.05,-5.17,2.01,.115),(.57,-5.10,2.19,.059),(1.00,-4.99,2.13,.005)]
    verts=[];faces=[]
    for x,y,z,r in control:
        for k in range(32):
            a=math.tau*k/32
            verts.append((x,y+r*math.cos(a),z+r*math.sin(a)))
    for j in range(len(control)-1):
        for k in range(32): faces.append((j*32+k,j*32+(k+1)%32,(j+1)*32+(k+1)%32,(j+1)*32+k))
    thorn=mesh('The curved thorn / symbolic foreground',verts,faces,black,True)
    sub=thorn.modifiers.new('Organic curve','SUBSURF')
    sub.levels=2
    sub.render_levels=2
    tube('Cord tied around the thorn',[(-1.5+.22*math.cos(a),-5.1+.20*math.sin(a),.39+.035*a) for a in [math.tau*i/80 for i in range(81)]],.024,cord)
    tube('Loose neck cord',[(-1.65,-5.15,.39),(-2.2,-5.7,.02),(-2.8,-6.3,-.01),(-3.1,-7.2,-.01),(-2.7,-7.7,-.01),(-1.3,-7.5,-.01),(-.8,-6.3,-.01),(-1.28,-5.1,.40)],.018,cord)
    # Boots in the advancing water recall the action, rather than placing a shrine.
    def boot(x,y,angle,tilt):
        before=set(s.objects)
        sphere('Boot / toe',(0,-.23,.19),(.19,.35,.14),leather)
        cube('Boot / sole',(0,-.12,.10),(.40,.83,.10),sole,.085)
        shaft=cyl('Boot / ankle',(0,.10,.38),.18,.53,leather,vertices=32)
        shaft.scale.y=.78
        rim=cyl('Boot / open cuff',(0,.10,.65),.186,.04,stitch,vertices=32)
        rim.scale.y=.80
        hole=cyl('Boot / cuff shadow',(0,.10,.674),.155,.009,sole,vertices=32)
        hole.scale.y=.78
        for z in [.30,.37,.44,.51,.58]:
            tube('Boot / laces',[(-.115,-.045,z),(.105,-.07,z+.045)],.013,stitch)
        bpy.ops.object.empty_add(location=(x,y,.07))
        parent=bpy.context.object
        parent.name='Boot in the waves'
        for o in set(s.objects)-before-{parent}: o.parent=parent
        parent.rotation_euler=(tilt,.0,angle)
    boot(1.4,.85,.6,1.15)
    boot(2.3,1.7,-.6,.85)
    cam=camera((7,-21,6),(0,0,1.3),12.0)
    cube('Distant atmospheric field',(0,30,12),(150,.1,80),sky,0)
    sun=cyl('Last red sun',(-7,25,1.8),1.3,.025,red,vertices=160)
    sun.rotation_euler=cam.rotation_euler
    area('Sun across wet sand',(-12,10,15),(0,-2,0),2300,8,(1,.62,.28))
    area('Blue sky',(1,-4,14),(0,0,0),1100,12,(.54,.78,1))
    s['literary_basis']='The Citadel of the Autarch: the beach, the curved thorn, sacred sand, and the boots thrown into the waves.'
    s['interpretation']='Symbolic composition. The enlarged thorn and its foreground placement are artistic choices, not a literal reconstruction.'

elif args.scene=='combray':
    porcelain=material('Ivory porcelain',(.73,.67,.50),.22,grain=.025)
    blue=material('Cobalt china line',(.025,.07,.13),.30)
    tea=material('Lime-flower tea',(.135,.073,.019),.13,.28)
    gold=material('Fine gilding',(.48,.285,.080),.23,.70)
    cake=material('Madeleine / baked shell',(.56,.265,.055),.83,grain=.85)
    crumb=material('Madeleine / golden folds',(.75,.46,.14),.9,grain=.6)
    table=material('Walnut tabletop',(.055,.037,.034),.57,grain=.32)
    stone=material('Combray / pale remembered stone',(.38,.42,.36),.83,grain=.45)
    roof=material('Slate roofs',(.052,.13,.17),.61,grain=.3)
    leaf=material('Gardens remembered',(.09,.16,.097),.91)
    wall=material('A cool room',(.062,.12,.16),.9)
    light=material('Morning window',(.65,.62,.43),.7,glow=1.7)
    cube('Table',(0,0,-.23),(50,50,.4),table,.02)
    # Open cup profile contains both the outside and the inner wall.
    lathe('Porcelain teacup',[(.12,.6),(.18,.72),(.36,.9),(.85,1.20),(1.35,1.35),(1.39,1.33),(1.34,1.28),(.85,1.12),(.42,.79),(.26,.56)],porcelain)
    lathe('Saucer',[(.02,.1),(.03,1.12),(.08,1.58),(.22,2.12),(.27,2.16),(.29,2.09),(.15,1.48),(.12,.1)],porcelain)
    for z,r,m in [(1.372,1.341,gold),(.25,2.13,gold),(.19,1.98,blue),(.46,.947,blue)]:
        tube('Hand-painted china ring',[(r*math.cos(a),r*math.sin(a),z) for a in [math.tau*i/180 for i in range(180)]],.014,m,True)
    handle=[]
    for i in range(80):
        a=-1.9+3.8*i/79
        handle.append((1.28+.69*math.cos(a),0,.83+.52*math.sin(a)))
    tube('Cup handle',handle,.115,porcelain)
    cyl('Tea surface',(0,0,1.22),1.265,.026,tea,vertices=128)
    # The shell-shaped cake has radiating grooves and a plump convex surface.
    vv=[];ff=[]
    for j in range(61):
        t=j/60
        r=.23+.57*math.sin(math.pi*t*.93)
        yy=-2.48+1.4*t
        for i in range(65):
            a=-math.pi/2+math.pi*i/64
            x=-1.25+r*math.sin(a)
            z=.12+.27*math.sin(math.pi*t)**.65*math.cos(a)
            z+=.019*math.cos(a*14)*math.sin(math.pi*t)
            vv.append((x,yy,z))
    for j in range(60):
        for i in range(64):
            a=j*65+i
            ff.append((a,a+1,a+66,a+65))
    mesh('Scallop-shell madeleine',vv,ff,cake,True)
    for k in range(25):
        sphere('A few crumbs',(-1.2+rng.uniform(-1,1),-2.15+rng.uniform(-.8,.4),.01),(rng.uniform(.014,.035),.027,.018),crumb)
    # Combray rising from tea visualizes Proust's own figurative description.
    def house(x,y,w,d,h):
        base=1.22
        cube('A remembered house',(x,y,base+h/2),(w,d,h),stone,.01)
        mesh('Slate roof',[(x-w*.58,y-d*.60,base+h),(x+w*.58,y-d*.60,base+h),(x,y-d*.60,base+h+.30),(x-w*.58,y+d*.60,base+h),(x+w*.58,y+d*.60,base+h),(x,y+d*.60,base+h+.30)],[(0,1,2),(3,5,4),(0,2,5,3),(2,1,4,5)],roof)
        for zz in [base+.20,base+.51]:
            for xx in [x-w*.23,x+w*.23]:cube('Tiny remembered window',(xx,y-d*.506,zz),(.075,.017,.13),blue,.007)
    for params in [(-.72,.11,.39,.42,.65),(.08,.35,.50,.39,.53),(.60,.15,.34,.42,.88),(-.35,-.31,.37,.3,.41),(.22,-.4,.30,.36,.37),(-.43,.60,.35,.40,.64)]:house(*params)
    # Church silhouette at the heart of Combray, with no modern landmark asserted.
    cube('Parish church tower',(-.14,.22,2.55),(.39,.37,2.4),stone,.008)
    cyl('Church spire',(-.14,.22,4.05),.38,.75,roof,top=0,vertices=4).rotation_euler[2]=math.pi/4
    for x in [-.24,-.04]:cube('Belfry', (x,.027,3.40),(.10,.02,.31),blue,.05)
    tube('Church cross',[(-.14,.22,4.43),(-.14,.22,4.73)],.013,gold)
    tube('Cross arm',[(-.24,.22,4.62),(-.04,.22,4.62)],.012,gold)
    for k in range(18):
        a=math.tau*k/18
        r=.80+rng.random()*.16
        sphere('Combray gardens',(r*math.cos(a),r*math.sin(a),1.38),(.11,.13,.22),leaf)
    # Gentle afternoon light through an ordinary window, with a long shadow.
    cube('Room wall',(0,6,4),(40,.18,20),wall,.01)
    cube('Window light',(-4,5.87,4.1),(3.7,.03,5.2),light,.01)
    for x in [-5.9,-4,-2.1]:cube('Window mullion',(x,5.75,4.1),(.08,.2,5.4),table,.01)
    for z in [1.45,4.1,6.75]:cube('Window crossbar',(-4,5.75,z),(3.9,.2,.09),table,.01)
    camera((7,-12,9),(0,.4,2.30),6.45)
    area('Window light',(-4,-2,8),(0,0,1),720,4,(1,.81,.53))
    area('Room fill',(5,-4,5),(0,0,1),220,5,(.50,.72,1))
    s['literary_basis']="Swann's Way, Combray: a shell-shaped madeleine and tea evoke aunt Leonie and the town; Proust describes Combray arising from the cup."
    s['interpretation']='The miniature town literally rising from the tea is a visual interpretation of the metaphor, not an event in the story.'
    s['work']='In Search of Lost Time / Marcel Proust'

elif args.scene=='casa':
    adobe=material('Weathered adobe',(.22,.17,.126),.97,grain=.95)
    pale=material('Patches of old plaster',(.33,.27,.19),.94,grain=.85)
    wood=material('Warped old boards',(.067,.049,.03),.86,grain=.65)
    dark=material('Unlit cells',(.006,.013,.014),.98)
    terracotta=material('Old roof tiles',(.26,.085,.041),.91,grain=.6)
    mortar=material('Dull mortar',(.106,.128,.115),.95,grain=.5)
    leaf=material('Orange leaves',(.018,.073,.051),.88,grain=.2)
    orange=material('Oranges in the courtyard',(.68,.19,.02),.69,grain=.35)
    iron=material('Rusty nails and rails',(.035,.034,.026),.71,.5)
    rag=material('Old bundles',(.105,.089,.062),.97,grain=.8)
    sky=material('Dusk above the Casa',(.031,.07,.105),.95,glow=.50)
    cube('Court floor',(0,0,-.16),(40,40,.3),mortar,0)
    for i in range(16):
        for j in range(20):
            x=-4+i*.52;y=-5+j*.53
            cube('Uneven paving',(x,y,rng.uniform(-.02,.0)),(.49,.50,.045),adobe if (i+j)%3==0 else mortar,.012)
    cube('Back wing',(0,4.3,3.2),(9,.65,6.4),adobe,.02)
    for x in [-4.4,4.4]:cube('Side wing',(x,.1,3.1),(.66,8.6,6.2),adobe,.02)
    # A U-shaped court with cells and windows repeatedly boarded or sealed.
    for side in [-1,1]:
        for j in range(6):
            y=-3.6+j*1.31
            cube('Cell door',(side*4.05,y,1.12),(.035,.71,2.15),dark,.04)
            for zz in [.7,1.5,2.0]:cube('Boards over cell doors',(side*4.02,y,zz),(.07,.84,.19),wood,.01,(.08*side,0,0))
            cube('Upstairs window',(side*4.05,y,4.60),(.03,.72,1.13),dark,.02)
            if j%2:
                for k in range(4):cube('Window boarded shut',(side*4.01,y,4.19+k*.27),(.06,.78,.23),wood,.02)
            else:
                cube('Window sealed with plaster',(side*4.0,y,4.60),(.055,.74,1.15),pale,.015)
        cube('Upper gallery',(side*3.50,.1,3.14),(1.43,8.5,.17),wood,.02)
        for y in [-3.8,-2.4,-1,1.1,2.5,3.8]:
            cube('Gallery posts',(side*2.85,y,3.65),(.08,.07,1.0),wood,.01)
        tube('Failing gallery rail',[(side*2.85,-4.1,4.13),(side*2.85,-1.7,4.13),(side*2.90,-1.12,3.85)],.052,wood)
        tube('Remaining gallery rail',[(side*2.85,.7,4.13),(side*2.85,4.1,4.13)],.052,wood)
    for j in range(7):
        x=-3.5+j*1.17
        cube('Rear cell door',(x,3.962,1.09),(.72,.04,2.12),dark,.035)
        for k in range(5):cube('Repeated boards',(x,3.922,.35+k*.37),(.80,.06,.30),wood,.02,(0,rng.uniform(-.06,.06),0))
        cube('Blind rear window',(x,3.958,4.62),(.71,.035,1.0),pale if j%2==0 else dark,.02)
    # Chips in plaster remain sparse; their uneven edges expose the older adobe.
    for k in range(95):
        x=rng.uniform(-4.3,4.3);z=rng.uniform(.2,6.1)
        if any(abs(x-(-3.5+j*1.17))<.45 and (z<2.25 or 4.05<z<5.2) for j in range(7)):continue
        points=[(x+rng.uniform(-.17,.17),3.958,z+rng.uniform(-.22,.22)) for _ in range(7)]
        points.sort(key=lambda v:math.atan2(v[2]-z,v[0]-x))
        mesh('Flaked plaster',points,[tuple(range(7))],pale)
    for side in [-1,1]:
        for j in range(44):
            y=-4.3+j*.2
            for k in range(4):
                tile=cyl('Half-round roof tile',(side*(4.6-k*.26),y,6.34+.07*k),.12,.32,terracotta,vertices=12)
                tile.rotation_euler[0]=math.pi/2
    # One orange tree anchors the court described in the excerpt.
    tx,ty=-.75,.5
    tube('Orange tree trunk',[(tx,ty,.02),(tx+.08,ty,1.2),(tx-.02,ty+.02,2.0),(tx+.20,ty,2.65)],.085,wood)
    for k in range(13):
        a=k*2.399
        end=(tx+.87*math.cos(a),ty+.72*math.sin(a),2.5+rng.uniform(-.35,.45))
        tube('Twisted branches',[(tx,ty,1.3),(tx+.32*math.cos(a),ty+.24*math.sin(a),2.0),end],.029,wood)
        for j in range(5):
            pos=(end[0]+rng.uniform(-.35,.35),end[1]+rng.uniform(-.3,.3),end[2]+rng.uniform(-.18,.32))
            sphere('Dense orange leaves',pos,(.28,.23,.16),leaf)
        sphere('Orange fruit',(end[0],end[1]-.06,end[2]-.18),(.085,.085,.085),orange)
    for k in range(6):sphere('Fallen oranges',(tx+rng.uniform(-1.2,1.2),ty+rng.uniform(-.8,.8),.062),(.067,.067,.06),orange)
    for j in range(5):
        o=sphere('Cloth-wrapped clutter',(2.60+rng.uniform(-.25,.2),1.4+j*.43,.30),(.40,.29,.32),rag)
        for k in range(2):
            tube('Bundle cord',[(o.location.x-.32,o.location.y-.14+k*.26,.30),(o.location.x,o.location.y-.14+k*.26,.62),(o.location.x+.32,o.location.y-.14+k*.26,.30)],.014,wood)
    cube('Dusk beyond the walls',(0,10,8),(60,.1,30),sky,0)
    camera((7.5,-15,12),(0,.5,2.8),10.5)
    area('Last light over courtyard',(-6,-3,12),(0,1,1),1500,7,(.56,.75,1))
    area('Warm reflected light',(3,1,7),(0,1,2),550,5,(1,.58,.25))
    s['literary_basis']='The Casa de la Encarnacion at La Chimba: adobe, damaged plaster, boarded and walled-up windows, upper galleries, and a U-shaped court with orange trees.'
    s['interpretation']='Imagined arrangement of details grounded in the authorized excerpt; not a map of the Casa.'
    s['work']='The Obscene Bird of Night / Jose Donoso'

if args.scene in ['matachin','shore']:s['work']='The Book of the New Sun / Gene Wolfe'
s['geometry']='Procedural geometry and materials authored for this profile study.'
s.render.filepath=str(BUILD/(args.scene+'-preview.png') if args.preview else ASSETS/(args.scene+'.png'))
bpy.ops.wm.save_as_mainfile(filepath=str(BUILD/(args.scene+'.blend')),compress=True)
bpy.ops.render.render(write_still=True)
